# coding: utf8
# Copyright (c) 2008-2009 gocept gmbh & co. kg
# See also LICENSE.txt

import PIL.Image
import StringIO
import pkg_resources
import unittest
import zeit.cms.testing
import zeit.content.image.test
import zeit.imp.interfaces
import zeit.imp.mask
import zeit.imp.source
import zope.app.testing.functional


imp_layer = zope.app.testing.functional.ZCMLLayer(
    pkg_resources.resource_filename(__name__, 'ftesting.zcml'),
    __name__, 'ImpLayer', allow_teardown=True)


class TestLayerMask(unittest.TestCase):

    def test_mask(self):
        # Create a 20x30 mask in an 150x100 image
        mask = zeit.imp.mask.Mask((150, 100), (20, 30))
        mask_data = mask.open('r').read()
        expected_data = pkg_resources.resource_string(
            __name__, 'test_mask.png')
        self.assertEquals(expected_data, mask_data,
                          "Mask doesn't match expected mask.")

    def test_mask_with_border(self):
        # Create a 20x30 mask in an 150x100 image
        mask = zeit.imp.mask.Mask((150, 100), (20, 30), border=True)
        mask_data = mask.open('r').read()
        expected_data = pkg_resources.resource_string(
            __name__, 'test_mask_border.png')
        self.assertEquals(expected_data, mask_data,
                          "Mask doesn't match expected mask.")

    def test_rect_box(self):
        mask = zeit.imp.mask.Mask((150, 100), (20, 30))
        self.assertEquals(((65, 35), (85, 65)), mask._get_rect_box())


class TestScaleSource(zope.app.testing.functional.BrowserTestCase):

    layer = imp_layer

    def setUp(self):
        super(TestScaleSource, self).setUp()
        zeit.cms.testing.setup_product_config(product_config)
        self.source = zeit.imp.source.ScaleSource()

    def test_scale_source(self):
        scales = list(self.source)
        self.assertEquals(7, len(scales))
        scale = scales[0]
        self.assertEquals('450x200', scale.name)
        self.assertEquals('450', scale.width)
        self.assertEquals('200', scale.height)
        self.assertEquals(u'Aufmacher groß (450×200)', scale.title)


class TestCrop(zope.app.testing.functional.BrowserTestCase):

    layer = imp_layer

    def setUp(self):
        super(TestCrop, self).setUp()
        self.setSite(self.getRootFolder())
        self.group = (
            zeit.content.image.test.create_image_group_with_master_image())
        self.crop = zeit.imp.interfaces.ICropper(self.group)

    def tearDown(self):
        self.setSite(None)
        super(TestCrop, self).tearDown()

    def get_histogram(self, image):
        histogram = image.histogram()
        r, g, b = histogram[:256], histogram[256:512], histogram[512:]
        return r, g, b

    def test_invalid_filter_raises_valueerror(self):
        self.assertRaises(ValueError, self.crop.add_filter, 'foo', 1)

    def test_brightness_filter(self):
        # Factor 0 produces a solid black image. The histogram has only black
        # in it
        self.crop.add_filter('brightness', 0)
        image = self.crop.crop(200, 200, 0, 0, 200, 200)
        r, g, b = self.get_histogram(image)
        self.assertEquals(40000, r[0])
        self.assertEquals(40000, g[0])
        self.assertEquals(40000, b[0])
        self.assertEquals(0, sum(r[1:]))
        self.assertEquals(0, sum(g[1:]))
        self.assertEquals(0, sum(b[1:]))

    def test_color_filter(self):
        # Factor 0 gives a black and white image, so the channels are equal
        self.crop.add_filter('color', 0)
        image = self.crop.crop(200, 200, 0, 0, 200, 200)
        r, g, b = self.get_histogram(image)
        self.assertEquals(r, g)
        self.assertEquals(r, b)

    def test_contrast_filter(self):
        # A contrast factor of 0 produces a solid gray image:
        self.crop.add_filter('contrast', 0)
        image = self.crop.crop(200, 200, 0, 0, 200, 200)
        r, g, b = self.get_histogram(image)
        self.assertEquals(40000, sum(r))
        self.assertEquals(40000, sum(g))
        self.assertEquals(40000, sum(b))
        self.assertEquals(40000, r[156])
        self.assertEquals(40000, g[156])
        self.assertEquals(40000, b[156])

    def test_sharpness_filter(self):
        # Testing the sharpnes is not quite trival. We just check that the
        # histograms have changed:
        self.crop.add_filter('sharpness', 0)
        image = self.crop.crop(200, 200, 0, 0, 200, 200)
        r_smooth, g, b = self.get_histogram(image)

        # Create the sharp image now
        self.crop.filters[:] = []
        self.crop.add_filter('sharpness', 1000)
        image = self.crop.crop(200, 200, 0, 0, 200, 200)
        r_sharp, g, b = self.get_histogram(image)
        self.assertNotEqual(r_smooth, r_sharp)

    def test_store_without_crop_raises(self):
        self.assertRaises(RuntimeError, self.crop.store, 'foo')

    def test_store(self):
        self.crop.crop(200, 200, 0, 0, 200, 200)
        image = self.crop.store('foo')
        self.assertTrue(zeit.content.image.interfaces.IImage.providedBy(image))
        self.assertEquals(['group-foo.jpg', 'master-image.jpg'],
                          self.group.keys())

    def test_border_applied_after_filters(self):
        # The border must be applied after the filters. To verify this we
        # create an image with no contrast which is solid gray. The border adds
        # some black.
        self.crop.add_filter('contrast', 0)
        image = self.crop.crop(200, 200, 0, 0, 200, 200, border=True)
        r, g, b = self.get_histogram(image)
        self.assertNotEquals(40000, r[156])
        self.assertNotEquals(40000, g[156])
        self.assertNotEquals(40000, b[156])
        self.assertNotEquals(0, r[0])
        self.assertNotEquals(0, g[0])
        self.assertNotEquals(0, b[0])


scale_xml_path = pkg_resources.resource_filename(__name__, 'scales.xml')
product_config = {'zeit.imp': {'scale-source': 'file://%s' % scale_xml_path}}


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestLayerMask))
    suite.addTest(unittest.makeSuite(TestScaleSource))
    suite.addTest(unittest.makeSuite(TestCrop))
    return suite
