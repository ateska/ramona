Features
========

- ramonactl command line usage is compatible with init.d scripts (start/stop/restart/status/...)
	- Also user can specify 'filtering' of start/stop/restart/status scope by:
```bash
./console start program-name1 program-name2 ...
```

- Console can be started without start of server and also server can be started without launch of any program
- Each program is launched in dedicated process group
- configuration is ConfigParser compatible
- priority (order) in which programs are started/stopped
- Following environment variables are available:
	- RAMONA_CONFIGS (filled by console, list of config files as given on command line or by default mechanism, delimiter is ';')
	- RAMONA_SECTION (name of [program:?] section in config that is relevant for current program)

- Force start/restart of programs in 'FATAL' state (-f option)
- Console is able to re-establish connection when server goes down during console run-time
- When ramona server is exiting, it has to try to terminate all childs (using stop command)
- Ramona server terminates after stopping all child programs if console stop command is issued in non-interactive mode
- start command has option -S to launch server only (no program is started ... usable during development)
- @tool support (in methods in console_app class)
- @proxy_tool support (in methods in console_app class)
- working directory is changed during console start to the location of console app script (should be root of the app)
- immediate/yield modes of start/stop/restart commands
- core dump enabled stop of program
- Automatic (configurable) restart of failed program
- [program:x] command now can contain environment variable reference (e.g. ${HOME}) that will be expanded; also [env] is taken in account
- [program:x]'directory' option (change working directory prior program start)
- [program:x]'umask' option

Console
-------
- ramona console is embeddable in custom python app + it is extendable to provide similar functionality as 'pan.sh':
```python
class MyConsoleApp(ramona.console_app):

	@ramona.tool
	def unittests(self):
		'Seek for all unit tests and execute them'
		import unittest
		tl = unittest.TestLoader()
		ts = tl.discover('.', '__utest__.py')

		tr = unittest.runner.TextTestRunner(verbosity=2)
		res = tr.run(ts)

		return 0 if res.wasSuccessful() else 1
```

Logging
-------
- logging configuration:

```ini
[program:x]
stdin=[<null>]
stdout=[<null>|<stderr>|<logdir>|FILENAME]
stderr=[<null>|<stdout>|<logdir>|FILENAME]
```
Options:
  * &lt;null> (redirect to /dev/null)
  * &lt;stderr> (redirect stdout to stderr)
  * &lt;stdout> (redirect stderr to stdout)
  * &lt;logdir>  (file in [server]logdir named [ident]-out.log, [ident]-err.log respectively [ident].log)

Defaults:
```
stdin=<null>
stdout=<stderr>
stderr=<logdir>
```

- log location is given as directory by:
	1. [server] logdir option
	2. environment variable LOGDIR

- (-s/--silent and -d/--debug) command-line options
- tail command
	- it works even when output is redirected or null
- log rotate (options logmaxsize and logbackups) [logmaxsize is not hard limit just a trigger for rotate]
- print "STARTING" and "EXITED" banners to log_err
- tail '-f' mode 

Configuration
-------------
- [program:x] disabled=true options
- section [env] in config defines environment variables (blends them with actual environment vars)

```ini
[env]
PYTHONPATH=./libraries
CLASSPATH=
```

Empty variable (e.g. CLASSPATH in previous example) will explicitly remove mentioned environment variable

- includes in config files:
	- primary file is given by -C switch (app. level config) + user application class - both part of user application distribution
	- secondary (optional) files is given by -c switch (site level config) + [general]include configuration option 
	- [general]include format is: =file1.conf:file2.conf:<siteconf>:... (default is <siteconf> only)
	- [general]include has also 'magic' option <siteconf> that delivers platform specific locations of the config:
		- ./site.conf
		- [prefix]/etc/[appname].conf (Linux|MacOSX)
- Application name in configuration ([general] appname)
- Some options uses 'magic' values (&lt;magic>)
- [program:x] 'processgroup' switch for using/not-using process group approach (default is on)


Mailing to admin
----------------
- Scan output streams of the program for keywords (by default 'error', 'fatal', 'exception') and send email when such event occurs
- Config sample (from [program:x]): logscan_stdout=error>mailto:foo2@bar.com,fatal>now,exception>now,warn>daily

HTTP frontend
-------------
- standalone process
- displays states of programs 
- allows to start/stop/restart each or all of them
- allows displaying tail of log files 
- basic authentication

Configuration:
- The HTTP frontend is added to configuration file as any other program, only with the special `command=<httpfend>`.
- Configuration sample including comments:

```ini
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
# SHA example. To generate use for example: echo -n "secret" | sha1sum
#password={SHA}e5e9fa1ba31ecd1ae84f75caaa474f3a663f05f4
```