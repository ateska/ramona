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


.. _config-ramonahttpfend:

[program:ramonahttpfend]
------------------------

Example:

.. code-block:: ini
  
  [program:ramonahttpfend]
  command=<httpfend>

  # IP address/hostname where the HTTP frontend will listen
  host=127.0.0.1
  
  # Port where the HTTP frontend will listen
  port=5588
  
  # Use username and password options only if you want to enable basic authentication
  username=admin
  
  # Can get either plain text or a SHA1 hash, if the password starts with {SHA} prefix
  password=pass



``host``
	
  IP address or hostname, where the Ramona HTTP frontend will listen.
  Use ``0.0.0.0`` to make Ramona HTTP frontend listen on IP addresses of all network interfaces.

  *Default*:  ``localhost``

  *Required*:  No

``port``

  Port on which the Ramona HTTP frontend will listen.
  
  *Default*:  ``5588``

  *Required*:  No
  
``username``
  
  Username used for authentication to Ramona HTTP frontend. 
  The authentication will be required only if the ``username``
  option is used.
  
  *Default*:  No default

  *Required*:  No
  
``password``
  
  Password to be used in combination with ``username`` for authentication. 
  If ``username`` option is used, the the ``password`` has to be specified as well --
  Ramona HTTP frontend will fail to start otherwise.
  
  The value can be either a plain text password or a SHA hash of the password.
  The SHA password hash has to be prefixed with ``{SHA}`` prefix, for example:

  .. code-block:: ini
  
     password={SHA}e5e9fa1ba31ecd1ae84f75caaa474f3a663f05f4
  
  which is a hash for word ``secret``. To generate the hash to be used for the configuration,
  you can use the following command (works on Linux):
  
  .. code-block:: sh
  
     echo -n "secret" | sha1sum
  
  *Default*:  No default

  *Required*:  No
  