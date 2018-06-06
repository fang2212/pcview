from distutils.core import setup
from Cython.Distutils import build_ext
from distutils.extension import Extension

setup(
    cmdclass = {'build_ext': build_ext},
    ext_modules = [
        Extension("pcview_client", sources=["pcview_client.pyx"])
    ]
) 
