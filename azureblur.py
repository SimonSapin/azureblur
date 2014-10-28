import os
import cffi


def _init():
    root = os.path.join(os.path.dirname(__file__))
    src = os.path.join(root, 'src')
    moz2d = os.path.join(root, 'moz2d')
    with open(os.path.join(src, 'azureblur.h')) as fd:
        declarations = '''
            struct AlphaBoxBlur;  // Opaque
            typedef struct AlphaBoxBlur AlphaBoxBlur;
        ''' + fd.read()
    ffi = cffi.FFI()
    ffi.cdef(declarations)
    azureblur = ffi.verify(
        declarations,
        sources=[
            os.path.join(src, 'azureblur.cpp'),
            os.path.join(moz2d, 'Blur.cpp'),
            os.path.join(moz2d, 'DataSurfaceHelpers.cpp'),
        ],
        include_dirs=[moz2d],
        extra_compile_args=['-std=gnu++0x'])
    return ffi, azureblur

ffi, azureblur = _init()


result = azureblur.azureblur_calculate_blur_radius(200, 300)
print(result.width, result.height)
