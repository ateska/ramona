TODO list
=========

Design questions
----------------
- tail of log ... how to do that

Generic
-------
- (low prio): SSL (optional) for protecting console-server channel
- core dump enabled launch/kill
- Unify & document sys.exit codes 
- Reload/reset command (restarting ramona server)
- [program:x] disabled=true options + console command enable/disable to allow change status during runtime
- [tool:x] support
- Restart of failed program (configurable)

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

Logging
-------
- Support for SIGHUP (reopen log files OR reset fully)
- log rotate
- log rotate of Ramona server log (stdout/stderr redirection)

Configuration
-------------
- optional alterative configuration for environment variables: https://github.com/ateska/ramona/issues/2
- environment variables expansion in configuration

Watchdog
--------
- watchdog functionality (child process is signaling that is alive periodically)

Python specific
---------------
- native python program execution (using sys.executable)
- python version (minimal) check

Error reporting
---------------
- Scan output streams of the program for keywords (by default 'error', 'fatal', 'exception') and send email when such event occurs

Mailing to admin
----------------
- Mailing issues to admin: https://github.com/ateska/ramona/issues/1

HTTP frontend
-------------
- Uptime instead of start time (maybe also in command-line console)
- Tail log
- Store static files in a way that setuptools and py2exe will work correctly. See: http://stackoverflow.com/questions/1395593/managing-resources-in-a-python-project
- (medium prio): Basic authentication
- (low prio): HTTPS
