Features
========

- ramonactl command line usage is compatible with init.d scripts (start/stop/restart/status/...)
- Console can be started without start of subprocesses
- Creates it's own progress group (Unix)
- configuration is ConfigParser compatible


Logging
-------
- logging configuration:


```
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

Configuration
-------------
- section [env] in config defines environment variables (blends them with actual environment vars)
```
[env]
PYTHONPATH=./libraries
CLASSPATH=
```
Empty variable (e.g. CLASSPATH in previous example) will explicitly remove mentioned environment variable