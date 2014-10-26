import os
import cffi


def _init():
    root = os.path.join(os.path.dirname(__file__))
    src = os.path.join(root, 'src')
    with open(os.path.join(src, 'azureblur.h')) as fd:
        declarations = fd.read()
    ffi = cffi.FFI()
    ffi.cdef(declarations)
    azureblur = ffi.verify(
        declarations,
        sources=[os.path.join(src, source) for source in [
            'Blur.cpp', 'azureblur.cpp'
        ]],
        include_dirs=[src])
    return ffi, azureblur


ffi, azureblur = _init()
del _init


print(azureblur.azureblur_new())
