#+
# Distutils script to install HarfPy. Invoke from the command line
# in this directory as follows:
#
#     python3 setup.py install
#
# Written by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
#-

import sys
import distutils.core
from distutils.command.build import \
    build as std_build

class my_build(std_build) :
    "customization of build to perform additional validation."

    def run(self) :
        try :
            class dummy :
                pass
            #end dummy
            dummy.__doc__ = "something"
        except AttributeError :
            sys.stderr.write("This module requires Python 3.3 or later.\n")
            sys.exit(-1)
        #end try
        super().run()
    #end run

#end my_build

distutils.core.setup \
  (
    name = "HarfPy",
    version = "0.8",
    description = "language bindings for HarfBuzz, for Python 3.3 or later",
    author = "Lawrence D'Oliveiro",
    author_email = "ldo@geek-central.gen.nz",
    url = "http://github.com/ldo/harfpy",
    py_modules = ["harfbuzz"],
    cmdclass =
        {
            "build" : my_build,
        },
  )
