import os
import io
from setuptools import setup

setup(
    name='azureblur',
    version='0.1',
    url='https://github.com/SimonSapin/azureblur',
    license='MPL2',
    description='The triple box blur implementation from Firefox’s moz2d/Azure, with Python bindings.',
    long_description=io.open(
        os.path.join(os.path.dirname(__file__), 'README.rst'),
        encoding='utf-8',
    ).read(),
    install_requires=['cffi'],
    packages=['azureblur'],
    package_data={'azureblur': ['src/*', 'moz2d/*.*', 'moz2d/*/*']},
)
