#+
# Distutils script to install HarfPy. Invoke from the command line
# in this directory as follows:
#
#     python3 setup.py install
#
# Written by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
#-

import distutils.core

distutils.core.setup \
  (
    name = "HarfPy",
    version = "0.5",
    description = "language bindings for HarfBuzz, for Python 3.3 or later",
    author = "Lawrence D'Oliveiro",
    author_email = "ldo@geek-central.gen.nz",
    # url = "http://github.com/ldo/harfpy",
    py_modules = ["harfbuzz"],
  )
