from setuptools import setup, find_packages
from codecs import open
from os import path

version="0.0.1a3"
# Get the long description from the README file
here = path.abspath(path.dirname(__file__))
with open(path.join(here, '../README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='ircbuilder',
    version=version,
    description='Python API for Minetest server with ircbuilder mod',
    long_description=long_description,
    url='https://github.com/timcu/ircbuilder',
    author="D Tim Cummings",
    author_email='dtimcummings@gmail.com',  # Optional
    license='MIT',
    classifiers=[ 
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Education',
        'Intended Audience :: Developers',
        'Topic :: Games/Entertainment',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
#        'Programming Language :: Python :: 3.6',
    ],

    keywords='minetest irc',  
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    python_requires='>=3',
    include_package_data=True,
)
