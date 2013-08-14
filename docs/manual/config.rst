Configuration
=============

Configuration is build the way that user program(s) can share the same configuration file(s) with Ramona system. Configuration is compatible with Python ConfigParser_. These are basic configuration files that use structure similar to what you would find on Microsoft Windows INI files.

.. _ConfigParser : http://docs.python.org/library/configparser.html


Application and site level configuration
----------------------------------------

Ramona supports split of configuration options into *application* and *site* level configuration. In this concept, application development team provides *application level configuration* as a part of source code and users are given by an option to provide their own *site level configurations* that can override or enhance application level configurations.

Both  *application* and *site* level configuration are supplied in form of files. Name (including full file path) of application level configuration file is provided by user application. Site configuration file name is derived based on table bellow.

*Application* and *site* level configuration as syntactically equal. 

See ``[general]`` :attr:`include` *<siteconf>* option for implementation details.


Platform selector
-----------------

Sometimes you wish to have different configurations for different platforms (basically OSes).
This is possible thru *platform selector* postfix mechanism that is provided by Ramona.
You can define platform-specific values optinally together with generic ones. In such a case, matching platform value is used instead of generic option.

Syntax is ``option@selector=value``.

List of selectors:

   ===================== ================
   System                Selector
   ===================== ================
   Linux                 ``linux``
   Windows               ``windows``
   Mac OS X              ``darwin``
   ===================== ================

.. note:: Platform names are based on Python ``platform.system()`` call.
  Lowercase form is used.

Examples:

.. code-block:: ini

  [program:ping]
  cmd=/sbin/ping
  cmd@windows=C:\Windows\System32\ping.exe


.. code-block:: ini

  [program:foolinux]
  disabled@windows=True


[general] section
-----------------

This section provides general configuration of Ramona-equiped application.


.. attribute:: appname

  Specifies name of application.

  Use of whitespaces is discourages (although possible). This value can become part of various file names, therefore it needs to respect syntax of file path and name.


  *Type*: string

  *Required*: Yes

  Example:

  .. code-block:: ini

    [general]
    appname=foobarapp


.. attribute:: include

  Ordered list of configuration files that should be loaded by Ramona. Separator of individual list items in this list is ';'.

  Magic value ``<siteconf>`` is expanded to following site level configuration file names:

    * ./site.conf
    * ./[appname]-site.conf
    * /etc/[appname].conf
    * ~/.[appname].conf

    Placeholder *[appname]* is expanded to value of ``[general]`` :attr:`appname` option.
    Relative path is evaluated from location of application main executable (e.g. containing ``ramona.console_app``).


  *Default*: ``<siteconf>``

  *Required*: No

  Example:

  .. code-block:: ini

    [general]
    include=<siteconf>


  .. code-block:: ini

    [general]
    include=/etc/foo.conf;/etc/bar.conf


.. attribute:: logdir

  TODO


.. attribute:: logmaxsize

  TODO


.. attribute:: logbackups

  TODO


.. attribute:: logcompress

  If `logcompress` configuration option is set to 1, the log files `xxx.log.2+` will be compressed
  using gzip compression.

  *Type*: boolean -- use "1", "yes", "true", and "on" for True, "0", "no", "false", and "off" for False
  
  *Default*: 1

  *Required*: No



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
  You can specify more network interfaces, protocols or ports, URIs are comma-separated. It should be synchronized with ``[ramona:console]`` :attr:`serveruri` option where configuration of Ramona client is specified, otherwise console connection fails.

  Supported connection variants:

  - UNIX sockets (where available)
  
    - optional parameter 'mode' specifies UNIX file permissions for created socket file system entry (in octal representation)

  - TCP IPv4
  - TCP IPv6

  *Default*: ``unix://.ramona.sock``

  *Default on Windows*: ``tcp://localhost:7788``

  *Required*: Yes (but default will work)

  Example:

  .. code-block:: ini

    [ramona:server]
    consoleuri=unix:///tmp/demoramona.sock;mode=0600,tcp://localhost:5566


.. attribute:: pidfile

  TODO
  You can use environment variables in form of ${var-name}.
  
  Example:

  .. code-block:: ini

    [ramona:server]
    pidfile=${TMP}/testramona.pid


.. attribute:: log

  TODO

  Example:

  .. code-block:: ini

    [ramona:server]
    log=/var/log/foo.log


  Magic variable '<logdir>'

  .. code-block:: ini

    [general]
    logdir=./log

    [ramona:server]
    log=<logdir>


  Will result in ./log/ramona.log



  .. code-block:: ini

    [general]
    logdir=./log

    [ramona:server]
    log=<logdir>/foo.log


  Will result in ./log/foo.log


.. attribute:: loglevel

  TODO


[ramona:console] section
------------------------

This section contains configuration used by Ramona console.


.. attribute:: serveruri

  One 'socket URIs' specifying Ramona server connection where Ramona console should connect to.
  It should be synchronized with ``[ramona:server]`` :attr:`consoleuri` option where relevant configuration of Ramona server is specified, otherwise console connection fails.

  Supported connection variants:

  - TCP IPv4
  - TCP IPv6
  - UNIX sockets (where available)

  *Default*: ``unix://.ramona.sock``

  *Default on Windows*: ``tcp://localhost:7788``

  *Required*: Yes (but default will work)

  Example:

  .. code-block:: ini

    [ramona:console]
    serveruri=unix:///tmp/demoramona.sock



.. attribute:: history

  Specifies the location of a command history file that will be used by Ramona console to store commands issued by its user.
  It allows users to use cursor keys to navigate up and down through the history list and re-use commands found there.
  History list is persistent and is available across program restarts.

  Generic description of command history feature can be found here: http://en.wikipedia.org/wiki/Command_history

  Empty configuration value disables history function completely.

  *Default*: (command history disabled)

  *Required*: No

  Example:

  .. code-block:: ini

    [ramona:console]
    history=./.appcmdhistory


[ramona:notify] section
-----------------------

TODO


.. attribute:: delivery

  TODO


.. attribute:: sender

  TODO


.. attribute:: receiver

  Default recipient of all notifications

.. attribute:: dailyat

  At what time the notifications should be used when ``daily`` period is used. The value is in the local timezone of your computer. Use the format ``HH:MM``

  *Default*:  ``09:00``

  *Required*:  No



[program:X] section
-------------------

TODO


.. attribute:: command

  expandvars
  TODO

  Example:

  .. code-block:: ini

    [ramona:server]
    command=ls -l /
    command@windows=dir c:\


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

  Example:
  
  .. code-block:: ini
  
    logscan_stdout=error>now:foo2@bar.com,fatal>now,exception>now,warn>daily:foo3@bar.com
   
  The meaning is following:
     - ``error>now:foo2@bar.com`` -- Whenever keyword *error* is found in the stdout, send an email immediatelly (now) to email address *foo2@bar.com*
     - ``fatal>now`` -- Whenever keyword *fatal* is found in the stdout, send an email immediatelly (now) to the default nofitication recipient configured in ``[ramona:notify]`` > receiver_ configuration option
     - ``exception>now`` -- same as fatal (above) just detecting different keyword (*exception*)
     - ``warn>daily:foo3@bar.com`` -- Cummulate all the log messages containing the keyword *warn* and send them to address *foo3@bar.com* once a day.


.. attribute:: logscan_stderr

  Same as logscan_stdout_, just scanning stderr stream.


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
  

