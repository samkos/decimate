Installation
============


Requirements
------------

*Decimate* should work with any cluster based on Unix operating systems which provides
Python 2.7 and using SLURM as a scheduler. It also depends on the python packages
numpy, pandas and clustershell.

In a further release, *Decimate* is planned to be compatible with Python 3 and no
dependency on numpy will be imposed.

Distribution
------------

*Decimate* is an open-source project distributed under the BSD
2-Clause "Simplified" License which means that many possibilities are
offered to the end user including the fact to embed *Decimate* in
one own software.

Its stable production branch is available via github at
https://github.com/KAUST-KSL/decimate, but its latest production and
development branch can be found at https://github.com/samkos/decimate

most up todate documentation about *Decimate* can be browsed at
http://decimate.readthedocs.io.


Installing *Decimate* using PIP
-------------------------------

Installing *Decimate* as root using PIP
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To install *Decimate* as a standard Python package using PIP [#]_ as root::

    $ pip install decimate

Or alternatively, using the source tarball::

    $ pip install decimate-0.9.x.tar.gz


.. _install-pip-user:

Installing *Decimate* as user using PIP
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To install *Decimate* as a standard Python package using PIP as an user::

    $ pip install --user decimate

Or alternatively, using the source tarball::

    $ pip install --user decimate-0.9.x.tar.gz

Then, you just need to update your ``PYTHONPATH`` environment variable to be
able to import the library and ``PATH`` to easily use the :ref:`tools`::

    $ export PYTHONPATH=$PYTHONPATH:~/.local/lib
    $ export PATH=$PATH:~/.local/bin

Configuration files are installed in ``~/.local/etc/decimate`` and are
automatically loaded before system-wide ones (for more info about supported
user config files, please see the :ref:`decimate-config` config section).

.. _install-source:

Source
------

Current source is available on  Github, use the following command to retrieve
the latest stable version from the repository::

    $ git clone -b prod git@github.com:samkos/decimate.git

and for the development version::

    $ git clone -b dev git@github.com:samkos/decimate.git


.. [#] pip is a tool for installing and managing Python packages, such as
   those found in the Python Package Index

.. _LGPL v2.1+: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
.. _Test Updates: http://fedoraproject.org/wiki/QA/Updates_Testing
.. _EPEL: http://fedoraproject.org/wiki/EPEL


