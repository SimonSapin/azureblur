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
    """
    Implementation of a triple box blur approximation of a Gaussian blur.

    A Gaussian blur is good for blurring because,
    when done independently in the horizontal and vertical directions,
    it matches the result that would be obtained
    using a different (rotated) set of axes.
    A triple box blur is a very close approximation of a Gaussian.

    This is a "service" class;
    the constructors set up all the information based on the values
    and compute the minimum size for an 8-bit alpha channel context.
    The callers are responsible for creating and managing the backing surface
    and passing the pointer to the data to the Blur() method.
    This class does not retain the pointer to the data
    outside of the :meth:`blur` call.

    A spread ``N`` makes each output pixel the maximum value of all source
    pixels within a square of side length ``2N+1`` centered on the output pixel.

    """
    def __init__(self, pointer):
        self._pointer = ffi.gc(pointer, azureblur.azureblur_delete)

    @classmethod
    def from_radiuses(cls, rect, spread_radius, blur_radius,
                      dirty_rect=None, skip_rect=None):
        """
        Constructs a box blur and computes the backing surface size.

        :param rect:
            The coordinates of the surface to create in device units.
            A ``(x, y, width, height)`` tuple.
        :param blur_radius:
            The blur radius in pixels.
            This is the radius of the entire (triple) kernel function.
            Each individual box blur has radius approximately 1/3 this value,
            or diameter approximately 2/3 this value.
            This parameter should nearly always be computed
            using :func:`calculate_blur_radius`, below.
            A ``(width, height)`` tuple.
        :param dirty_rect:
            An optional dirty rect, measured in device units, if available.
            This will be used for optimizing the blur operation.
            It is safe to pass nullptr here.
            A ``(x, y, width, height)`` tuple, or :obj:`None`.
        :param skip_rect:
            An optional rect, measured in device units,
            that represents an area where blurring is unnecessary
            and shouldn't be done for speed reasons.
            A ``(x, y, width, height)`` tuple, or :obj:`None`.

        """
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
        """
        Constructs a box blur and computes the backing surface size.

        :param rect:
            The coordinates of the surface to create in device units.
            A ``(x, y, width, height)`` tuple.

        **TODO:** document other parameters.

        """
        cls(azureblur_blur.azureblur_new_from_sigma(
            ffi.new('struct azureblur_rect*', rect),
            stride, sigma_x, sigma_y))

    def get_size(self):
        """
        Return the size, in pixels, of the 8-bit alpha surface we'd use.

        """
        size = azureblur.azureblur_get_size(self._pointer)
        return size.width, size.height

    def get_stride(self):
        """
        Return the stride, in bytes, of the 8-bit alpha surface we'd use.

        """
        return azureblur.azureblur_get_size(self._pointer)

    def get_rect(self):
        """
        Returns the device-space rectangle the 8-bit alpha surface covers.

        """
        rect = azureblur.azureblur_get_rect(self._pointer)
        return rect.x, rect.y, rect.width, rect.height

    def get_surface_allocation_size(self):
        """
        Return the minimum buffer size that should be given to Blur() method.
        If zero, the class is not properly setup for blurring.
        Note that this includes the extra three bytes
        on top of the ``stride * width``,
        where something like Gecko’s ``gfxImageSurface::GetDataSize()``
        would report without it,
        even if it happens to have the extra bytes.

        """
        return azureblur.azureblur_get_surface_allocation_size(self._pointer)

    def blur(self, data):
        """
        Perform the blur in-place
        on the surface backed by specified 8-bit alpha surface data.
        The size must be at least
        that returned by :meth:`get_surface_allocation_size`
        or bad things will happen.

        :param data:
            A pointer as a CFFI :class:`CData` object.

        """
        azureblur.azureblur_blur(self._pointer, data)


def calculate_blur_radius(standard_deviation_x, standard_deviation_y):
    """
    Calculates a blur radius that, when used with box blur,
    approximates a Gaussian blur with the given standard deviation.
    The result of this function should be used as the :obj`blur_radius`
    parameter to :meth:`AlphaBoxBlur.from_radiuses`.

    """
    size = azureblur.azureblur_calculate_blur_radius(
        standard_deviation_x, standard_deviation_y)
    return size.width, size.height


def test():
    width, height = calculate_blur_radius(1000, 2000)
    assert width == 2820
    assert height == 5640
