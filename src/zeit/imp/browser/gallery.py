# Copyright (c) 2008-2009 gocept gmbh & co. kg
# See also LICENSE.txt

import cjson
import zeit.cms.browser.view
import zeit.content.image.interfaces
import zeit.imp.browser.interfaces
import zeit.imp.browser.scale
import zeit.imp.source
import zope.cachedescriptors.property


class Imp(object):

    @property
    def width(self):
        return self.master_image.getImageSize()[0]

    @property
    def height(self):
        return self.master_image.getImageSize()[1]

    @zope.cachedescriptors.property.Lazy
    def master_image(self):
        return self.context.image

    def scales(self):
        return zeit.imp.source.ScaleSource()

    def colors(self):
        return zeit.imp.source.ColorSource()


class ImageBar(zeit.cms.browser.view.Base):

    def __call__(self):
        result = []
        # nyi
        return cjson.encode(result)


class ScaledImage(zeit.imp.browser.scale.ScaledImage):

    def __call__(self, width, height):
        self.context = self.context.image
        return super(ScaledImage, self).__call__(width, height)


class CropImage(zeit.imp.browser.scale.CropImage):

    def __call__(self, w, h, x1, y1, x2, y2, name, border=''):
        return super(CropImage, self).__call__(w, h, x1, y1, x2, y2, name, border)

    @property
    def image(self):
        return self.context.image