Features
========

- ramonactl command line usage is compatible with init.d scripts (start/stop/restart/status/...)
	- Also user can specify 'filtering' of start/stop/restart/status scope by:
```bash
./console start program-name1 program-name2 ...
```

- Console can be started without start of subprocesses
- Creates it's own progress group (Unix)
- configuration is ConfigParser compatible
- priority (order) in which programs are started/stopped
- Following environment variables are available:
	- RAMONA_CONFIGS (filled by console, list of config files as given on command line or by default mechanism, delimiter is ':')
	- RAMONA_SECTION (name of [program:?] section in config that is relevant for current program)

- Force start/restart of programs in 'FATAL' state (-f option)
- Console is able to re-establish connection when server goes down during console run-time
- When ramona server is exiting, it has to try to terminate all childs (using stop command)
- Ramona server terminates after stopping all child programs if console stop command is issued in non-interactive mode


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

Configuration
-------------
- section [env] in config defines environment variables (blends them with actual environment vars)

```ini
[env]
PYTHONPATH=./libraries
CLASSPATH=
```

Empty variable (e.g. CLASSPATH in previous example) will explicitly remove mentioned environment variable
