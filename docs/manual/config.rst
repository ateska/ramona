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

  .. note::

    Extensive logging can lead to unwanted loss of log files due to the rotation mechanism (e.g. log files quickly exceeding :attr:`logmaxsize`). To prevent this loss, set :attr:`logbackups` to ``inf`` and remove log files manually.


.. attribute:: logcompress

  If this configuration option is enabled, rotated log files ``foobar.log.2+`` will be compressed using gzip compression.

  *Type*: boolean
    - "1", "yes", "true", or "on" for enabling this feature
    - "0", "no", "false", and "off" for disabling
  
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

Setting an empty value to the variable causes the environment variable to be unset. See ``VARTOUNSET`` in the example below.

.. _`environment variables` : http://en.wikipedia.org/wiki/Environment_variable

Environment variable section example:

.. code-block:: ini

  [env]
  VARIABLE=value
  PYTHONPATH=./mylibs
  CLASSPATH=./myjars
  VARTOUNSET=


[ramona:server] section
-----------------------

This section configures Ramona server.


.. attribute:: consoleuri

  One or multiple 'socket URIs' specifying where Ramona server should listen for console connections.
  You can specify more network interfaces, protocols or ports, URIs are comma-separated. It should be synchronized with ``[ramona:console]`` :attr:`serveruri` option where configuration of Ramona client is specified, otherwise console connection fails.

  Supported connection variants:

  - UNIX sockets (where available)
  
    - optional `query string` argument 'mode' specifies UNIX file permissions for created socket file system entry (in octal representation)

  - TCP IPv4
  - TCP IPv6

  *Default*: ``unix://.ramona.sock``

  *Default on Windows*: ``tcp://localhost:7788``

  *Required*: Yes (but default will work)

  Example:

  .. code-block:: ini

    [ramona:server]
    consoleuri=unix:///tmp/demoramona.sock?mode=0600,tcp://localhost:5566


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


Notification system support immediate or delayed delivery. This can be configured using `actions`:
    - ``now``: notification is sent immediately
    - ``daily``: notification is stashed and sent in daily buld email

Deleayed notifications are stored in stashes which can be optionally persistent (survives eventual restart of a box).


.. attribute:: delivery

  URL specifies a default delivery method for notifications.

  Supported scheme is currently only 'smtp'. Format of URL is ``smtp://[username][:password]@host[:port]/[?parameters]``.
    - ``username``: the name of a user that will be used during a SMTP authorization (optional)
    - ``password``: the password of a user that will be used during a SMTP authorization (optional)
    - ``host``: the server name or IP address of SMTP MTA_ (**mandatory**)
    - ``port``: the port number to be used (optional, port 25 is default)
    - ``parameters``: set of parameters that will be used to configure STMP communication in form of URI query string - separated by ``&``

      * ``tls``: if this paramater is set to `1` then TLS (Transport Layer Security) mode of the STMP connection will be enabled

  .. _MTA: http://en.wikipedia.org/wiki/Message_transfer_agent


  A missing or empty value efectively disables default delivery option.

  *Default*: (empty)

  *Required*: No

  Example:

  .. code-block:: ini

    [ramona:notify]
    delivery=smtp://mail.example.com/

For real-life examples, see :ref:`smtp-configs`.


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


.. attribute:: notify_fatal

  Configure notification, that will be eventually triggered when any supervised program unexpectedly terminates and ends in FATAL state. This is done by specifying the `action`.

  You can override this option by `notify_fatal` entry in given ``[program:...]`` section.

  `action`
    - ``now``: immediately send email notification using defaults from [ramona:notify]
    - ``now:<email address>``: immediately send email notification to given email address
    - ``daily``: stash notification and eventually send in daily bulk email using defaults from [ramona:notify]
    - ``daily:<email address>``: stash notification and eventually send in daily bulk email given email address

  *Magic values* of `action` field:
    - ``<none>`` - don't publish any notification


  *Default*:  ``now``

  *Required*:  No

  Examples:

  .. code-block:: ini

    [ramona:notify]
    notify_fatal=now:admin@foo.bar.com


.. attribute:: dailyat

  At what time the notifications should be used when ``daily`` is used. The value is in the local timezone of your computer. Use the format ``HH:MM`` (24-hours).

  *Default*:  ``09:00``

  *Required*:  No

  Example:

  .. code-block:: ini

    [ramona:notify]
    dailyat=23:00


.. attribute:: stashdir

  Specify the directory where persistent stashes (files) are stored.

  *Magic values*:
    - ``<none>`` - disable persistence of notification stash (content will disapear when Ramona is restarted)

  *Default*:  ``<none>``

  *Required*:  No

  Example:

  .. code-block:: ini

    [ramona:notify]
    stashdir=/var/spool/ramona/stash


.. attribute:: logscan_stdout

.. attribute:: logscan_stderr

.. attribute:: logscan

  Global defaults for configuration values in  ``[program:...]`` section. If given, they will be used when program specific ones are not stated.



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
  See :ref:`nondaemon` section for more details.

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



.. attribute:: killby

  The sequence of signals that will be used to terminate a given program. Ramona server, when asked to stop a program, will send first signal (using POSIX `kill` functionality) from this sequence to given program and set its status to ``STOPPING``. If the program doesn't terminate, next signal from this sequence is sent after time defined by :attr:`stoptimeout`.

  POSIX signal names are used.

  When end of this sequence is reached, the KILL signal sent periodically to force program exit.

  *Default*:  ``TERM, INT, TERM, INT, TERM, INT, KILL``

  *Required*: No

  Example:

  .. code-block:: ini

    [program:foobarapp]
    killby=TERM,KILL


  List of useful signals:

  ======== =============
   Signal   Description
  ======== =============  
   TERM     The SIGTERM signal is sent to a process to request its termination. Unlike the SIGKILL signal, it can be caught and interpreted or ignored by the process. This allows the process to perform nice termination releasing resources and saving state if appropriate. It should be noted that SIGINT is nearly identical to SIGTERM.
   INT      The SIGINT signal is sent to a process when a user wishes to interrupt the process. This is equivalent to pressing Control-C.
   KILL     The SIGKILL signal is sent to a process to cause it to terminate immediately. In contrast to SIGTERM and SIGINT, this signal cannot be caught or ignored, and the receiving process cannot perform any clean-up upon receiving this signal.
   QUIT     The SIGQUIT signal is sent to a process when the user requests that the process perform a core dump. See :attr:`coredump`.
   ABRT     The SIGABRT signal is sent to a process to tell it to abort, i.e. to terminate. The signal is usually initiated by the process itself, but it can be sent to the process from Ramona server as well.
  ======== =============

.. attribute:: stoptimeout

  This defines a timeout interval between each terminate/kill attempt during ``STOPPING`` phase of a program life cycle. 

  *Default*: 3 *seconds*

  *Required*: No



.. attribute:: starttimeout

  How long to keep the program in a ``STARTING`` status prior switching in to ``RUNNING``.
  The program termination during ``STARTING`` period is considered as a fatal error, the termination during ``RUNNING`` period is considered as likely recoverable and restart attempt will be triggered.

  Value is in seconds and is an integer or a floating point number.

  *Default*: 0.5 *second*

  *Required*: No



.. attribute:: stdout

  Configures how to handle standard output stream of a program. Use one of magic values or specify filesystem path to file, where to store log of a stream.

  *Magic values*:
    - ``<null>`` - don't store standard output in any file
    - ``<stderr>`` - redirect standard output to standard error
    - ``<logdir>`` - use file in directory specified by :attr:`logdir`, name of the file is ``[programname]-out.log`` or ``[programname].log`` if standard error is redirected to stdout


  *Default*: ``<stderr>``

  *Required*: No



.. attribute:: stderr

  Configures how to handle standard error stream of a program. Use one of magic values or specify filesystem path to file, where to store log of a stream.

  *Magic values*:
    - ``<null>`` - don't store standard output in any file
    - ``<stdout>`` - redirect standard error to standard output
    - ``<logdir>`` - use file in directory specified by :attr:`logdir`, name of the file is ``[programname]-err.log`` or ``[programname].log`` if standard error is redirected to stdout


  *Default*: ``<logdir>``

  *Required*: No



.. attribute:: priority

  Priority is used to determine a sequence in which programs are started. Higher priority ensures sooner position in start sequence.

  Value has to be an integer, can be negative.

  *Default*: ``100``

  *Required*: No



.. attribute:: disabled

  Set program state to ``DISABLED`` - efectively excludes any option to start this program by Ramona server.

  *Type*: boolean
    - "1", "yes", "true", or "on" for disabling program
    - "0", "no", "false", and "off" for keeping it enabled

  *Default*: ``no``

  *Required*: No

  Example:

  .. code-block:: ini

    [program:foobarposix]
    disabled@windows=yes



.. attribute:: coredump

  If enabled, Ramona server sets ulimit (user limit) for `core file size` (``RLIMIT_CORE``) to infinite, efectively enabling creation of core dump file when process is terminated by QUIT signal. Actual core dump is requested by ``-c`` argument in :ref:`cmdline-stop`.

  *Type*: boolean
    - "1", "yes", "true", or "on" for enabling core dump program
    - "0", "no", "false", and "off" for keeping it disabled

  *Default*: ``no``

  *Required*: No



.. attribute:: autorestart

  Enables/disables auto-restart of the program. If enabled, Ramona server will automatically start the relevant supervised program when it terminates unexpectedly (e.g. crash of the program). If program is terminated using :ref:`cmdline-stop` command, it will not be restarted.

  *Type*: boolean
    - "1", "yes", "true", or "on" for enabling auto-restart feature
    - "0", "no", "false", and "off" for disabling auto-restart feature

  *Default*: ``no``

  *Required*: No



.. attribute:: processgroup

  If enabled, program will be started in dedicated process group by using POSIX ``setsid(2)`` call. If disabled, program will stay in process group of Ramona server.

  *Type*: boolean
    - "1", "yes", "true", or "on" for enabling creation of own process group
    - "0", "no", "false", and "off" for disabling creation of own process group

  *Default*: ``yes``

  *Required*: No

  **Available only on POSIX platforms.**



.. attribute:: logscan_stdout

  Configures log scanner for standard output stream. 
  See :ref:`features-logging` for more details. 

  Stream is scanned even if :attr:`stdout` is set to ``<null>``.

  Value is sequence of comma-separated (``,``) scanner rules. Each rule consist of `keyword` and `action` in format ``keyword>action``.

  `keyword`
    Case-insensitive string that the scanner is trying to detect in a scanned stream.

  `action`
    - ``now``: immediately send email notification using defaults from [ramona:notify]
    - ``now:<email address>``: immediately send email notification to given email address
    - ``daily``: stash notification and eventually send in daily bulk email using defaults from [ramona:notify]
    - ``daily:<email address>``: stash notification and eventually send in daily bulk email given email address


  Example:
  
  .. code-block:: ini
  
    logscan_stdout=error>now:foo2@bar.com,fatal>now,exception>now,warn>daily:foo3@bar.com
   
  The meaning is following:
     - ``error>now:foo2@bar.com`` -- Whenever keyword *error* is found in the stdout, send an email immediatelly (now) to email address *foo2@bar.com*
     - ``fatal>now`` -- Whenever keyword *fatal* is found in the stdout, send an email immediatelly (now) to the default nofitication recipient configured in ``[ramona:notify]`` :attr:`receiver` configuration option
     - ``exception>now`` -- same as fatal (above) just detecting different keyword (*exception*)
     - ``warn>daily:foo3@bar.com`` -- Cummulate all the log messages containing the keyword *warn* and send them to address *foo3@bar.com* once a day.



.. attribute:: logscan_stderr

  Same as logscan_stdout_, just scanning standard error stream.


.. attribute:: notify_fatal

  Configure notification, that will be eventually triggered when this program unexpectedly terminates and ends in FATAL state. This is done by specifying the `action`.

  `action`
    - ``now``: immediately send email notification using defaults from `[ramona:notify]`
    - ``now:<email address>``: immediately send email notification to given email address
    - ``daily``: stash notification and eventually send in daily bulk email using defaults from [ramona:notify]
    - ``daily:<email address>``: stash notification and eventually send in daily bulk email given email address

  *Magic values* of `action` field:
    - ``<none>`` - don't publish any notification
    - ``<global>`` - use `notify_fatal` configuration from `[ramona:notify]` section


  *Default*:  ``<global>``

  *Required*:  No

  Examples:

  .. code-block:: ini

    [program:foobarcrasher]
    notify_fatal=daily:admin@foo.bar.com


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
  password=password


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
  

