Developer information
=====================

To package python distribution and upload to test pypi from virtual environment containing twine::

  pip install wheel
  rm -R build dist ircbuilder.egg-info
  python setup.py sdist       # only required for source distribution
  python setup.py bdist_wheel
  twine upload --repository-url https://test.pypi.org/legacy/ dist/*.whl

To install from test pypi::

  pip install --index-url https://test.pypi.org/simple/ ircbuilder==0.0.8

To upload to pypi::

  twine upload dist/*.whl

To install from pypi::

  pip install ircbuilder

