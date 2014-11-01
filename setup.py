# coding: utf8
import os
import io
from setuptools import setup
from distutils.command.build import build


class cffi_build(build):
    """
    This is a shameful hack to ensure that cffi is present
    when we specify ext_modules.
    We can't do this eagerly because setup_requires hasn't run yet.
    """
    def finalize_options(self):
        from azureblur import ffi
        self.distribution.ext_modules = [ffi.verifier.get_extension()]
        build.finalize_options(self)


setup(
    name='azureblur',
    version='0.1',
    url='https://github.com/SimonSapin/azureblur',
    license='MPL2',
    maintainer='Simon Sapin',
    maintainer_email='simon.sapin@exyr.org',
    description='The triple box blur implementation from Firefox’s moz2d/Azure, with Python bindings.',
    long_description=io.open(
        os.path.join(os.path.dirname(__file__), 'README.rst'),
        encoding='utf-8',
    ).read(),
    install_requires=['cffi'],
    setup_requires=['cffi'],
    packages=['azureblur'],
    package_data={'azureblur': ['src/*', 'moz2d/*.*', 'moz2d/*/*']},
    zip_safe=False,
    cmdclass={'build': cffi_build},
)
