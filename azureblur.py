import cffi

ffi = cffi.FFI()
ffi.cdef('''
    int azureblur_new();
''')
azureblur = ffi.dlopen('build/azureblur.so')
print(azureblur.azureblur_new())
