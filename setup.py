#!/usr/bin/env python 
# vim: set sts=4 sw=4 et:

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


version = "0.0.1"

setup (name = "tupelo",
    description = "Random code around a card game called Tuppi",
    version = version,
    author = "Jari Tenhunen",
    author_email = "jari.tenhunen@iki.fi",
    license = "BSD",
    packages = ['tupelo'],
    py_modules = ['qcommon'],
    scripts = ['qtupelo.py', 'tupelo.py', 'tupelo-server.py'],
    platforms="Python 2.4 and later.",
    test_suite = "nose.collector"
    )



