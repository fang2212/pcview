from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [
        Extension("draw",  ["draw.py"]),
        Extension("file_handler",  ["file_handler.py"]),
        Extension("pcview_client",  ["pcview_client.py"]),
    #   ... all your modules that need be compiled ...
    ]

setup(
    name = 'pcview_client',
    cmdclass = {'build_ext': build_ext},
    ext_modules = ext_modules,
)
