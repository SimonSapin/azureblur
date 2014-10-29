import os
import cffi


_root = os.path.join(os.path.dirname(__file__))
_src = os.path.join(_root, 'src')
_moz2d = os.path.join(_root, 'moz2d')
with open(os.path.join(_src, 'azureblur.h')) as fd:
    _declarations = '''
        struct AlphaBoxBlur;  // Opaque
        typedef struct AlphaBoxBlur AlphaBoxBlur;
    ''' + fd.read()
ffi = cffi.FFI()
ffi.cdef(_declarations)
azureblur = ffi.verify(
    _declarations,
    sources=[
        os.path.join(_src, 'azureblur.cpp'),
        os.path.join(_moz2d, 'Blur.cpp'),
        os.path.join(_moz2d, 'DataSurfaceHelpers.cpp'),
    ],
    include_dirs=[_moz2d],
    extra_compile_args=['-std=gnu++0x'])


class AlphaBoxBlur(object):
    def __init__(self, pointer):
        self._pointer = ffi.gc(pointer, azureblur.azureblur_delete)

    @classmethod
    def from_radiuses(cls, rect, spread_radius, blur_radius,
                      dirty_rect=None, skip_rect=None):
        cls(azureblur_blur.azureblur_new_from_radiuses(
            ffi.new('struct azureblur_rect*', rect),
            ffi.new('struct azureblur_intsize*', spread_radius),
            ffi.new('struct azureblur_intsize*', blur_radius),
            ffi.new('struct azureblur_rect*', dirty_rect)
                if dirty_rect else ffi.NULL,
            ffi.new('struct azureblur_rect*', skip_rect)
                if skip_rect else ffi.NULL))

    @classmethod
    def from_sigma(cls, rect, stride, sigma_x, sigma_y):
        cls(azureblur_blur.azureblur_new_from_sigma(
            ffi.new('struct azureblur_rect*', rect),
            stride, sigma_x, sigma_y))

    def get_size(self):
        size = azureblur.azureblur_get_size(self._pointer)
        return size.width, size.height

    def get_stride(self):
        return azureblur.azureblur_get_size(self._pointer)

    def get_rect(self):
        rect = azureblur.azureblur_get_rect(self._pointer)
        return rect.x, rect.y, rect.width, rect.height

    def get_surface_allocation_size(self):
        return azureblur.azureblur_get_surface_allocation_size(self._pointer)

    def blur(self, cdata):
        azureblur.azureblur_blur(self._pointer, cdata)


def calculate_blur_radius(standard_deviation_x, standard_deviation_y):
    size = azureblur.azureblur_calculate_blur_radius(
        standard_deviation_x, standard_deviation_y)
    return size.width, result.size
