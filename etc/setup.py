from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [
        Extension("config",  ["config.py"]),
        Extension("define",  ["define.py"]),
    #   ... all your modules that need be compiled ...
    ]

setup(
    name = 'config',
    cmdclass = {'build_ext': build_ext},
    ext_modules = ext_modules,
)
