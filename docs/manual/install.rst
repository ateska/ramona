Installation
============

Prerequisites
-------------

- Python 2.7+ (currently not compatible with Python 3)
- pyev_ (install via ``pip install pyev`` or ``easy_install pyev``)

.. _pyev: http://pypi.python.org/pypi/pyev


Installation using **pip**
--------------------------

.. code-block:: bash

  pip install ramona


Installation using **easy_install**
-----------------------------------

.. code-block:: bash

  easy_install ramona

Manual installation
-------------------

.. _Pypi: http://pypi.python.org/pypi/ramona

1. Download ramona*.zip or ramona*.tar.gz from PyPi_.
2. Unpack downloaded archive into empty directory
3. Open command-line interface (shell, cmd.exe) and go to the unpacked directory
4. Execute following command: ``python setup.py install``

Inclusion of Ramona code into your project
------------------------------------------

Alternatively you can include Ramona source code folder directly into your project, effectively removing an external dependency.

1. Download ramona*.zip or ramona*.tar.gz from PyPi_.
2. Unpack downloaded archive into empty directory
3. Copy ``ramona`` subdirectory into your project directory root.

Target directory structure for project called *foo* looks as follow::

  foo/
    bin/
    share/
    src/
    docs/
    ramona/
    foo.py
    foo.conf

