#!/usr/bin/env python 
# vim: set sts=4 sw=4 et:

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


VERSION = "0.0.5"

setup (name = "tupelo",
    description = "Random code around a card game called Tuppi",
    version = VERSION,
    author = "Jari Tenhunen",
    author_email = "jari.tenhunen@iki.fi",
    license = "BSD",
    packages = ['tupelo'],
    scripts = ['scripts/tupelo', 'scripts/tupelo-server'],
    data_files = [('share/tupelo/www', ['www/index.html', 'www/tupelo.js',
            'www/tupelo-main.js', 'www/tupelo.css', 'www/buttons.css']),
            ('share/tupelo/www/img', ['www/img/bg.png', 'www/img/bg-button.gif'])],
    platforms="Python 2.5 and later.",
    test_suite = "nose.collector"
    )

