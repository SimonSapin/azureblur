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

The image below is `generated
<https://github.com/SimonSapin/azureblur/blob/master/azureblur/__main__.py>`_
with `cairocffi <https://pythonhosted.org/cairocffi/>`_
and this library for blurring the shadow.

.. image:: ../sample.png
