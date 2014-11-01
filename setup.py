from setuptools import setup

setup(
    name='azureblur',
    version='0.1',
    url='https://github.com/SimonSapin/azureblur',
    license='MPL2',
    install_requires=['cffi'],
    packages=['azureblur'],
    package_data={'azureblur': ['src/*', 'moz2d/*.*', 'moz2d/*/*']},
)
