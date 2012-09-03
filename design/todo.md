TODO list
=========

Design questions
----------------
- tail of log ... how to do that

Generic
-------
- SSL (optional) for protecting console-server channel
- core dump enabled launch/kill
- Unify sys.exit codes
     - 2 = configuration error
- When ramona daemon is exiting, it has to try to terminate all childs (using stop functionality first and then kill whole process group)

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
- log rotate
- log rotate of Ramona server log (stdout/stderr redirection)

Configuration
-------------
- configuration files - app.conf & site.conf - describe differences, implement
- includes in config files
- ConfigParser changes case of the keys/name to lower-case (e.g. PATH=/bin -> ['path']='/bin') 
- optional alterative configuration for environment variables: https://github.com/ateska/ramona/issues/2
- environment variables expansion in configuration

Watchdog
--------
- watchdog functionality (child process is signaling that is alive periodically)

Python specific
---------------
- native python program execution (using sys.executable)

Error reporting
---------------
- Scan output streams of the program for keywords (by default 'error', 'fatal', 'exception') and send email when such event occurs

Mailing to admin
----------------
- Mailing issues to admin: https://github.com/ateska/ramona/issues/1

HTTP frontend
-------------
- eventual HTTP frontend is subprocess using standard socket API to communicate with daemon
