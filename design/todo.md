TODO list
=========

Design questions
----------------
- tail of log ... how to do that

Generic
-------
- SSL (optional) for protecting console-server channel
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
- Application name in configuration (general)
- includes in config files:
	- primary file is given by -C switch (app. level config) + user application class - both part of user application distribution
	- secondary (optional) files is given by -c switch (site level config) + [general]include configuration option 
	- [general]include format is: =file1.conf:file2.conf:<siteconf>:... (default is <siteconf> only)
	- [general]include has also 'magic' option <siteconf> that delivers platform specific locations of the config:
		- ./site.conf
		- [prefix]/etc/[appname].conf (Linux|MacOSX)

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
- Find nice favicon.ico
- Use application name from configuration in page title (title tag and h1 tag too)
- Tail log
- Store static files in a way that setuptools and py2exe will work correctly. See: http://stackoverflow.com/questions/1395593/managing-resources-in-a-python-project
- (medium prio): Basic authentication
- (low prio): HTTPS
