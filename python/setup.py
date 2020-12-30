from setuptools import setup, find_packages
from codecs import open
from os import path
from ircbuilder.version import VERSION

# Get the long description from the README file
here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='ircbuilder',
    version=VERSION,
    description='Python API for Minetest server with irc_builder mod',
    long_description=long_description,
    url='https://github.com/timcu/irc_builder',
    author="D Tim Cummings",
    author_email='dtimcummings@gmail.com',  # Optional
    license='MIT',
    classifiers=[ 
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',
        'Intended Audience :: Education',
        'Intended Audience :: Developers',
        'Topic :: Games/Entertainment',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],

    keywords='minetest irc',  
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    python_requires='>=3.6',
)
