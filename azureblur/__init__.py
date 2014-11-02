# coding: utf8
import os
import array
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
        os.path.join(_moz2d, 'BlurSSE2.cpp'),
        os.path.join(_moz2d, 'Factory.cpp'),
    ],
    define_macros=[('USE_SSE2', '1')],
    include_dirs=[_moz2d],
    libraries=['stdc++'],
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
        return cls(azureblur.azureblur_new_from_radiuses(
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
        return cls(azureblur.azureblur_new_from_sigma(
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
        return azureblur.azureblur_get_stride(self._pointer)

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

    def blur_array(self, data_array):
        r"""
        Perform the blur in-place
        on the surface backed by specified 8-bit alpha surface data.

        :param data_array:
            A :class:`array.array` of at least
            :meth:`get_surface_allocation_size` byte-sized items.
        :raises:
            :exc:`ValueError` if the the array is too small
            or its items are not byte-sized.

        On PyPy, because of the moving garbage collector,
        :meth:`array.array.buffer_info` is the only reliable way to get
        a pointer to a chuck of writable memory allocated from Python.

        Usage example:

        .. code-block:: python

            import azureblur
            blur = azureblur.AlphaBoxBlur.from_radiuses(...)
            alloc_size = blur.get_surface_allocation_size()
            data = array.array('B', b'\x00' * alloc_size)
            blur.blur_array(data)

        """
        if data_array.itemsize != 1:
            raise ValueError('Array must contain bytes.')
        if len(data_array) < self.get_surface_allocation_size():
            raise ValueError(
                'Array must be at least `blur.get_surface_allocation_size()` '
                'bytes long')
        address, _ = data_array.buffer_info()
        self.blur_pointer(ffi.cast('uint8_t*', address))

    def blur_pointer(self, data_pointer):
        """
        Perform the blur in-place
        on the surface backed by specified 8-bit alpha surface data.
        The size must be at least
        that returned by :meth:`get_surface_allocation_size`
        or bad things will happen.

        :param data_pointer:
            A ``uint8_t*`` pointer as a CFFI :class:`CData` object.

        """
        azureblur.azureblur_blur(self._pointer, data_pointer)


def calculate_blur_radius(standard_deviation_x, standard_deviation_y):
    """
    Calculates a blur radius that, when used with box blur,
    approximates a Gaussian blur with the given standard deviation.
    The result of this function should be used as the :obj:`blur_radius`
    parameter to :meth:`AlphaBoxBlur.from_radiuses`.

    :returns: A blur radius as a ``(width, height)`` tuple.

    """
    size = azureblur.azureblur_calculate_blur_radius(
        standard_deviation_x, standard_deviation_y)
    return size.width, size.height


def test_calculate():
    assert calculate_blur_radius(1000, 2000) == (2820, 5640)


def test_parameters():
    blur = AlphaBoxBlur.from_radiuses(
        spread_radius=(1, 2),
        blur_radius=(4, 8),
        rect=(-16, 32, 64, 128),
    )

    # Size of rect, inflated by spread + blur radiuses
    assert blur.get_size() == (74, 148)
    assert blur.get_size() == (64 + 2 * (1 + 4), 128 + 2 * (2 + 8))

    # Next multiple of 4 after width == 74
    assert blur.get_stride() == 76
    assert blur.get_stride() == (74 + 3) // 4 * 4

    # rect inflated by spread + blur radiuses
    assert blur.get_rect() == (-21, 22, 74, 148)
    assert blur.get_rect() == (
        -16 - (1 + 4),
        32 - (2 + 8),
        64 + 2 * (1 + 4),
        128 + 2 * (2 + 8)
    )
    assert blur.get_rect()[2:] == blur.get_size()

    # stride * height + (3 bytes for algorithm overflow)
    assert blur.get_surface_allocation_size() == 11251
    assert blur.get_surface_allocation_size() == 76 * 148 + 3


def test_blur():
    blur = AlphaBoxBlur.from_radiuses(
        rect=(0, 0, 4, 1),
        spread_radius=(0, 0),
        blur_radius=(2, 2),
    )
    assert blur.get_size() == (8, 5)
    assert blur.get_stride() == 8
    alloc_size = blur.get_surface_allocation_size()
    data = array.array('B', b'\x00' * alloc_size)
    data[8 * 2 + 2] = 0xFF
    data[8 * 2 + 3] = 0xFF
    data[8 * 2 + 4] = 0xFF
    data[8 * 2 + 5] = 0xFF
    blur.blur_array(data)
    for i, byte in enumerate(data[:8 * 5]):
        assert 0 < byte < 0xFF, (i, byte)
    # XXX How reliable is this?
    assert data == array.array('B', [
        1, 6, 13, 19, 19, 13, 6, 1,
        5, 20, 41, 57, 57, 41, 20, 5,
        6, 27, 55, 77, 77, 55, 27, 6,
        5, 20, 41, 57, 57, 41, 20, 5,
        1, 6, 13, 19, 19, 13, 6, 1,
        0, 0, 0
    ])


def benchmark():
    blur = AlphaBoxBlur.from_radiuses(
        rect=(0, 0, 3000, 1000),
        spread_radius=(0, 0),
        blur_radius=(5, 5),
    )
    data = array.array('B', b'\x00' * blur.get_surface_allocation_size())
    for y in range(5, 10):
        for x in (30, 50):
            data[100 * y + x] = 0xFF

    import timeit
    print(min(timeit.repeat(lambda: blur.blur_array(data), number=10)))
