Configuration
=============

Configuration is build the way that user program(s) can share the same configuration file(s) with Ramona system. Configuration is compatible with Python ConfigParser_. These are basic configuration files that use structure similar to what you would find on Microsoft Windows INI files.

.. _ConfigParser : http://docs.python.org/library/configparser.html

Application and site level configuration
----------------------------------------

Ramona supports split of configuration options into *application* and *site* level configuration. In this concept application development team provides *application level configuration* as a part of source code and users are given an option to provide their own *site level configurations* that can override or enhance application level configurations.

Practically application level configuration can specify file(s) to optionally include - these files can provide site level configuration.

Application and site level configuration as syntactically equal.


[general] section
-----------------

TODO


.. attribute:: appname

  TODO


.. attribute:: include

  TODO

Separator is ';'


.. attribute:: logdir

  TODO


.. attribute:: logmaxsize

  TODO


.. attribute:: logbackups

  TODO



[env] section
-------------

Environment section allows to specify `environment variables`_ that will be added to the environment variable set that applies to running Ramona server.

These variables can be also used in other options via ``${VARNAME}`` placeholders.

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


.. attribute:: consoleuri

  One or multiple 'socket URIs' specifying where Ramona server should listen for console connections.
  You can specify more network interfaces, protocols or ports, URIs are comma-separated. It should be synchronized with [ramona:console] option serveruri (where configuration of client side is specified), otherwise console connection fails.

  Supported connection variants:

  - UNIX sockets
  
    - optional parameter 'mode' specifies UNIX file permissions for created socket file system entry (in octal representation)

  - TCP IPv4
  - TCP IPv6

  *Default*: ``unix://.ramona.sock``

  *Required*: Yes (but default will work)

  Example:

  .. code-block:: ini

    [ramona:server]
    consoleuri=unix:///tmp/demoramona.sock;mode=0600,tcp://localhost:5566


.. attribute:: pidfile

  TODO


.. attribute:: log

  TODO


.. attribute:: loglevel

  TODO



[ramona:notify] section
-----------------------

TODO


.. attribute:: delivery

  TODO


.. attribute:: sender

  TODO


.. attribute:: receiver

  TODO



[program:X] section
-------------------

TODO


.. attribute:: command

  expandvars
  TODO


.. attribute:: directory

  expandvars
  TODO


.. attribute:: umask

  TODO


.. attribute:: starttimeout

  TODO


.. attribute:: stoptimeout

  TODO


.. attribute:: killby

  TODO


.. attribute:: stdin

  TODO


.. attribute:: stdout

  TODO


.. attribute:: stderr

  TODO


.. attribute:: priority

  TODO


.. attribute:: disabled

  TODO


.. attribute:: coredump

  TODO


.. attribute:: autorestart

  TODO


.. attribute:: processgroup

  TODO


.. attribute:: logscan_stdout

  TODO


.. attribute:: logscan_stderr

  TODO


.. _config-ramonahttpfend:

[program:ramonahttpfend]
------------------------

Example:

.. code-block:: ini
  
  [program:ramonahttpfend]
  command=<httpfend>

  # Where the HTTP frontend will listen
  listen=tcp://localhost:5588
  
  # Use username and password options only if you want to enable basic authentication
  username=admin
  
  # Can get either plain text or a SHA1 hash, if the password starts with {SHA} prefix
  password=pass


.. attribute:: listen
	
  One or multiple 'socket URIs', where the Ramona HTTP frontend will listen. 
  You can specify more network interfaces, protocols or ports, URIs are comma-separated.
    
  Supported connection variants:

  - UNIX sockets
  
    - optional parameter 'mode' specifies UNIX file permissions for created socket file system entry (in octal representation)

  - TCP IPv4: For example: ``tcp://127.0.0.1:4455``
  - TCP IPv6: For example: ``tcp://[::1]:8877``


  *Default*:  ``tcp://localhost:5588``

  *Required*:  No


.. attribute:: username
  
  Username used for authentication to Ramona HTTP frontend. 
  The authentication will be required only if the ``username``
  option is used.
  
  *Default*:  No default

  *Required*:  No


.. attribute:: password
  
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
  
