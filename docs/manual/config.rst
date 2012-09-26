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

Example:

.. code-block:: ini
  
  [program:ramonahttpfend]
  command=<httpfend>

  # IP address/hostname where the HTTP frontend should listen
  host=127.0.0.1
  
  # Port where the HTTP frontend should listen
  port=5588
  
  # Use username and password options only if you want to enable basic authentication
  username=admin
  
  # Can get either plain text or a SHA1 hash, if the password starts with {SHA} prefix
  password=pass



``port``

  A TCP host:port value or (e.g. ``127.0.0.1:9001``) on which
  supervisor will listen for HTTP/XML-RPC requests.
  :program:`supervisorctl` will use XML-RPC to communicate with
  :program:`supervisord` over this port.  To listen on all interfaces
  in the machine, use ``:9001`` or ``*:9001``.

  *Default*:  No default.

  *Required*:  Yes.

  *Introduced*: 3.0
