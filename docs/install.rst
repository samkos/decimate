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

The most recent documentation about *Decimate* can be browsed at
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



Installing *Decimate* using Anaconda
------------------------------------

*Decimate* is also available in Anaconda from the hpc4all_
channel. It can be installed with the command::

   $ conda install -c hpc4all decimate 


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
.. _hpcall: https://anaconda.org/hpc4all

