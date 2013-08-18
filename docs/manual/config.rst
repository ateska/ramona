Configuration
=============

Configuration is build the way that user program(s) can share the same configuration file(s) with Ramona system. Configuration is compatible with Python ConfigParser_. These are basic configuration files that use structure similar to what you would find on Microsoft Windows INI files.

.. _ConfigParser : http://docs.python.org/library/configparser.html

.. note:: 
  You are free to blend configuration options of your application with Ramona ones. This is the design intention and it simplifies the structure of a configuration and therefore it makes maintenance significantly easier.

  Ideally there should be only one application level configuration file and maybe another one for site level in a whole application.


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

.. note::

  Feel free to add any other configuration values that are usefull for your application. Ramona will silently ignore them. Also your application can of course use configuration values required by Ramona.


.. attribute:: appname

  Specifies name of application.

  .. note::
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

  Specifies path of a log directory on a filesystem. This value is then stored as a ``<logdir>`` magic value and can be used in other log configuration options.

  It allows you to ensure that all logs that are produced by Ramona (including logs from program standard streams) will be stored in single directory.

  *Magic values*:
    - ``<env>``: Use the ``LOGDIR`` environment variable to specify a location of a logging directory. If not present, use a current directory (e.g. ``.`` on POSIX) relatively to Ramona application.

  *Default*: ``<env>``

  *Required*: Yes *(but default works fine)*

  Example:

  .. code-block:: ini

    [general]
    logdir=/var/log/foo



.. attribute:: logmaxsize

  Maximum log file size prior being rotated.

  Basically a log file grows without bound unless action is taken and this can cause problems. A solution to this generic problem of log file growth is log rotation. This involves t moving of an existing log file that reach certain size to some other file name and starting fresh with an empty log file. After a period the old log files get thrown away.

  The pattern is that if a log file name is ``foobar.log`` then the first (the freshest) rotated log file name is ``foobar.log.1``, the second freshest is ``foobar.log.2`` and so on. Rotated log files are renamed in a process of a log rotation increasing a tail number by one to make a space for a newly rotated file.

  Magic values:
    - ``<inf>``: disables log rotation function.

  *Default*: 536870912 (512Mb)

  *Required*: Yes *(but default works fine)*

  Example:

  .. code-block:: ini

    [general]
    logmaxsize=1000000000


.. attribute:: logbackups

  Number of archived rotated log files, rotated log files with a higher tail number that this config value will be removed.

  Magic values:
    - ``<inf>``: infinite number of rotated log files (disabling removal of old rotated log files)

  *Default*: 3

  *Required*: Yes *(but default works fine)*

  Example:

  .. code-block:: ini

    [general]
    logmaxsize=1000000
    logbackups=2

  Then

  ::

    foobar.log
    foobar.log.1
    foobar.log.2
    foobar.log.3 <-- this one will be removed


.. attribute:: logcompress

  If this configuration option is enabled, rotated log files ``foobar.log.2+`` will be compressed using gzip compression.

  *Type*: boolean
    - "1", "yes", "true", or "on" for enabling this feature
    - "0", no", "false", and "off" for disaling
  
  *Default*: "on"

  *Required*: No

  Example:

  .. code-block:: ini

    [general]
    logmaxsize=1000000
    logbackups=5
    logcompress=off


[env] section
-------------

Environment variables section allows to specify `environment variables`_ that will be added to the environment of Ramona server. These will be also propagated to supervised programs during their start.

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

This section configures Ramona server.


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

  Specifies location of file with `process identified`_ of Ramona server. This file can be eventually used by other processes or users to look it up.

  If no or empty value is provided, no pid file is created.

  .. _`process identified`: http://en.wikipedia.org/wiki/Process_identifier
  
  .. note ::
    
    You can use environment variables in form of ``${VARNAME}``.

  *Default*: (empty)

  *Required*: No


  Example:

  .. code-block:: ini

    [ramona:server]
    pidfile=${TMP}/testramona.pid



.. attribute:: log

  Specifies where to store a log file of Ramona server.

  *Default*: ``<logdir>``

  *Required*: Yes

  Example:

  .. code-block:: ini

    [ramona:server]
    log=/var/log/foo.log


  Magic variables:
    - ``<logdir>``: can be used anywhere in a path to refer to a value of ``[general]`` :attr:`logdir` .

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

  Defines a log level respectively a verbosity of Ramona server.

  Following log levels can be used:
    ============= =============================================================================
     Level         Meaning
    ============= =============================================================================
     ``DEBUG``     Detailed information, typically of interest only when diagnosing problems. 
     ``INFO``      Confirmation that things are working as expected.
     ``WARNING``   An indication that something unexpected happened, or indicative of some problem in the near future. The software is still working as expected.
     ``ERROR``     Due to a more serious problem, the software has not been able to perform some function.
     ``CRITICAL``  A serious error, indicating that the program itself may be unable to continue running.
    ============= =============================================================================

  *Default*: ``INFO``

  *Required*: No

  Example:

  .. code-block:: ini

    [ramona:server]
    loglevel=DEBUG


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

This is configuration of Ramona notification sub-system. This component (part of Ramona server) is reponsible for sending out email notifications about pre-configured events.

.. note::

  Python ``smtplib`` module is used to handle SMTP connectivity.


.. attribute:: delivery

  URL specifies a default delivery method for notifications.

  Supported scheme is currently only 'smtp'. Format of URL is ``smtp://[username][:password]@host[:port]/[;parameters]``.
    - ``username``: the name of a user that will be used during a SMTP authorization (optional)
    - ``password``: the password of a user that will be used during a SMTP authorization (optional)
    - ``host``: the server name or IP address of SMTP MTA_ (**mandatory**)
    - ``port``: the port number to be used (optional, port 25 is default)
    - ``parameters``: set of parameters that will be used to configure STMP communication

      * ``tls``: if this paramater is set to `1` then TLS (Transport Layer Security) mode of the STMP connection will be enabled

  .. _MTA: http://en.wikipedia.org/wiki/Message_transfer_agent


  A missing or empty value efectively disables default delivery option.

  *Default*: (empty)

  *Required*: No

  Examples:

  .. code-block:: ini

    [ramona:notify]
    delivery=smtp://user:password@smtp.gmail.com:587/;tls=1


  .. code-block:: ini

    [ramona:notify]
    delivery=smtp://mail.example.com/



.. attribute:: sender

  The email address of a sender which will be used in ``From:`` field of the notification email.

  Magic value ``<user>`` will result in email address constructed from a name of an OS user used to launch Ramona server.

  *Default*: ``<user>``

  *Required*: No

  Examples:

  .. code-block:: ini

    [ramona:notify]
    sender=ramona@app.foobar.com


.. attribute:: receiver

  The default email address of an recipient of notifications.

  You can provide multiple email addresses separated by comma (``,``).

  *Default*: (empty)

  *Required*: No

  Examples:

  .. code-block:: ini

    [ramona:notify]
    receiver=admin@foobar.com,moniting@foobar.com


.. attribute:: dailyat

  At what time the notifications should be used when ``daily`` period is used. The value is in the local timezone of your computer. Use the format ``HH:MM`` (24-hours).

  *Default*:  ``09:00``

  *Required*:  No

  Examples:

  .. code-block:: ini

    [ramona:notify]
    dailyat=23:00



[program:...] section
---------------------

This section of an configuration allows to define program, that will be supervised by Ramona (started, monitored and eventually stopped) including various parameters that describes intended runtime behaviour of given program.

The ``...`` in ``[program:...]`` section name should be substituted by name of supervised program. Name should be in ASCII using uppercase and lowecase letters, numbers, underscore (``_``) but no whitespaces.

.. note::

  Common configuration of Ramona typically contains more than one of ``[program:...]`` section.

Example:

.. code-block:: ini

  [program:frontend]
  cmd=./frontend.py

  [program:backend]
  cmd=./backend.py
  
  [program:integration1]
  cmd=./integration1.py
  


.. attribute:: command

  The command that is used to start a program. Ramona server will issue this command in order to change state of a program to ``STARTING`` (and eventual ``RUNNING``) status.

  The command can be either absolute (e.g. ``/path/to/foobarapp``), relative (``./bin/foobarapp``) or just application executable name (e.g. ``foobarapp``). If last option is used, the environment variable ``${PATH}`` will be searched for the executable. Programs can accept arguments, e.g. ``/path/to/foobarapp foo bar``. 

  Supervised programs should themselves not be daemons_, as Ramona server assumes it is responsible for daemonizing itself.

  .. [TODO]: Link to ondaemonizing of Subprocesses (in tools.rst)

  .. _daemons: http://en.wikipedia.org/wiki/Daemon_(computing)

  *Default*: (none)

  *Required*: Yes

  Example:

  .. code-block:: ini

    [program:dirlist]
    command=ls -l /
    command@windows=dir c:\

  .. note::

    You can take benefit of environment variables expansion when defining this option.

    .. code-block:: ini

      [program:fooapp]
      command=./fooapp -t ${TMPDIR}



.. attribute:: directory

  The directory that program should be started in. Ramona server will change a working directory to this value just prior launching relevant program. Change of directory is local only for given program.

  If no or empty value is given, no change of directory is performed, th program will be launched in a working directory of Ramona server.

  *Default*: (none)

  *Required*: No

  .. note::

    You can take benefit of environment variables expansion when defining this option.

    .. code-block:: ini

      [program:fooapp]
      directory=${TMPDIR}



.. attribute:: umask

  Specifies *mask* of the program. Mask controls which file permissions are set for files and directories when they are created.

  If no or empty value is given, to umask is set.

  **Available only on POSIX platforms.**

  *Default*: (none)

  *Required*: No

  Example:

  .. code-block:: ini

    [program:foobarapp]
    umask=002



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

The HTTP frontend is added to configuration file as any other program, only with the special option `command=<httpfend>`.

By default configuration, it is available at http://localhost:5588

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

  - TCP IPv4: For example: ``tcp://127.0.0.1:4455``
  - TCP IPv6: For example: ``tcp://[::1]:8877``
  - UNIX sockets  
    
    - optional parameter 'mode' specifies UNIX file permissions for created socket file system entry (in octal representation)


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
  

