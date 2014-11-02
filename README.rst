azureblur
#########

The `triple box blur <http://dbaron.org/log/20110225-blur-radius>`_
implementation from Firefox’s
`moz2d / Azure <https://wiki.mozilla.org/Platform/GFX/Moz2D>`_,
with Python bindings.

* Documentation: https://pythonhosted.org/azureblur/
* Source and issues: https://github.com/SimonSapin/azureblur
* Install with ``pip install azureblur``.
  This requires ``libffi-dev``, ``python-dev``, and a C/C++ compiler.
  See `CFFI documentation <http://cffi.readthedocs.org/en/release-0.8/>`_.

This library only supports 2D raster images
with a single channel of one byte per pixel.
Such images are typically used as a *mask*
that affects the alpha (transparency) channel of some other source.

See for example `the code that generates the image below
<https://github.com/SimonSapin/azureblur/blob/master/azureblur/__main__.py>`_,
using this library for blurring the shadow
and the `cairocffi <https://pythonhosted.org/cairocffi/>`_ 2D graphics library.

.. image:: sample.png
