**********
Installing
**********

Before installing ``DyNetx``, you need to have setuptools installed.


Note
----

In case of misaligned versions between pypl and GitHub, the documentation will refer to the GitHub version.

=============
Quick install
=============

Get ``DyNetx`` from the Python Package Index at pypl_.

or install it with

.. code-block:: python

    pip install dynetx

and an attempt will be made to find and install an appropriate version that matches your operating system and Python version.

You can install the development version with

.. code-block:: python

    pip install git://github.com/GiulioRossetti/dynetx.git

======================
Installing from source
======================

You can install from source by downloading a source archive file (tar.gz or zip) or by checking out the source files from the GitHub source code repository.

``DyNetx`` is a pure Python package; you don’t need a compiler to build or install it.

-------------------
Source archive file
-------------------
Download the source (tar.gz or zip file) from pypl_  or get the latest development version from GitHub_ 

Unpack and change directory to the source directory (it should have the files README.txt and setup.py).

Run python setup.py install to build and install

------
GitHub
------
Clone the DyNetx repository (see GitHub_ for options)

.. code-block:: python

    git clone https://github.com/GiulioRossetti/dynetx.git

Change directory to ndlib

Run python setup.py install to build and install

If you don’t have permission to install software on your system, you can install into another directory using the --user, --prefix, or --home flags to setup.py.

For example

.. code-block:: python

    python setup.py install --prefix=/home/username/python

or

.. code-block:: python

    python setup.py install --home=~

or

.. code-block:: python

    python setup.py install --user

If you didn’t install in the standard Python site-packages directory you will need to set your PYTHONPATH variable to the alternate location. See http://docs.python.org/2/install/index.html#search-path for further details.

============
Requirements
============
------
Python
------

To use DyNetx you need Python 2.7, 3.2 or later.

The easiest way to get Python and most optional packages is to install the Enthought Python distribution “Canopy” or using Anaconda.

There are several other distributions that contain the key packages you need for scientific computing. 

-----------------
Required packages
-----------------
The following are packages required by ``DyNetx``.

^^^^^^^^
NetworkX
^^^^^^^^
``DyNetx`` extends the networkx python library adding dynamic network facilities.

Download: http://networkx.github.io/download.html


.. _pypl: https://pypi.python.org/pypi/dynetx/
.. _GitHub: https://github.com/GiulioRossetti/dynetx/
