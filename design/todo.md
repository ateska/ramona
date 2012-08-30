TODO list
=========

Generic
-------
- SSL (optional) for protecting console-server channel
- core dump enabled launch/kill
- priority (order) in which programs are launched ...
- Unify sys.exit codes
     - 2 = configuration error
- When ramona daemon is exiting, it has to try to terminate all childs (using stop functionality first and then kill whole process group)
- Launch priority (start/stop job sequence)

Windows
-------
- working on Windows (based on pyev / libev?)
- daemonizing is not available on Windows - provide Windows Service option instead

Console
-------
- ramonactl is embeddable in custom python app + it is extendable to provide similar functionality as 'pan.sh':

```python
class MyConsoleApp(ramona.console_app):
	pass
	# Add 'unittest' option ...
	# Add 'floader' option ...
```

- recover (in running console) from situation when server is shutdown during run

Logging
-------
- (--log-level) command-line option
- log rotate

Configuration
-------------
- configuration files - app.conf & site.conf - describe differences, implement
- ConfigParser changes case of the keys/name to lower-case (e.g. PATH=/bin -> ['path']='/bin') 
- optional alterative configuration for environment variables:
```
[env]
FOO=bar

[env:alternative1]
BAR=foo

[program:one]
# Uses [env]

[program:two]
# Uses [env:alternative1]
env=&alternative1
```

- environment variables expansion in configuration
- includes in config files

Watchdog
--------
- watchdog functionality (child process is signaling that is alive periodically)

Python specific
---------------
- native python program execution (using sys.executable)

HTTP frontend
-------------
- eventual HTTP frontend is subprocess using standard socket API to communicate with daemon

Error reporting
---------------
- Scan output of the program for keywords (by default 'error', 'fatal', 'exception') and send email when such event occurs
