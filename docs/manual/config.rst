Configuration
=============

Configuration is build the way that user program(s) can share the same configuration file(s) with Ramona system. Configuration is compatible with Python ConfigParser_. These are basic configuration files that use structure similar to what you would find on Microsoft Windows INI files.

.. _ConfigParser : http://docs.python.org/library/configparser.html

Application and site level configuration
----------------------------------------

Configuration also supports split into *application level configuration* and *site level configuration*. In this concept application development team provides *application level configuration* as a part of source code and users are given an option to provide their own *site level configurations* that can override or enhance application level configurations.

Practically application level configuration can specify file(s) to optionally include - these files can provide site level configuration.

Application and site level configuration as syntactically equal.


[general] section
-----------------

TODO


[env] section
-------------

Environment section allows to specify `environment variables`_ that will be added to the environment variable set that applies to running Ramona server.

.. _`environment variables` : http://en.wikipedia.org/wiki/Environment_variable

Environment variable section example:

.. code-block:: ini

  [env]
  VARIABLE=value
  PYTHONPATH=./mylibs
  CLASSPATH=./myjars


[ramona:server] section
-----------------------

TODO


[ramona:notify] section
-----------------------

TODO


[program:X] section
-------------------

TODO


[program:ramonahttpfend]
------------------------

TODO

