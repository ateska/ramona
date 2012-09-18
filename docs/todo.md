TODO list
=========

Generic
-------
- exitcodes option for autorestart (autorestart=1,2,3)
- (low prio): SSL (optional) for protecting console-server channel
- ulimit/resources (similar to core dump) -> minfds, minprocs
- Unify & document sys.exit codes 
- Reload/reset command (restarting ramona server)
- [tool:x] support (how to do this properly - config is read __after__ arguments are parsed)
- console command enable/disable to allow change status during runtime
- [program:x] disabled 'magic' options:
	 - e.g. <on-platform linux:mac>
- [tool:x] - support floader case (hand-over to other executable)
- test Ramona how it runs in out-of-diskspace conditions
- 'user' option - If ramona runs as root, this UNIX user account will be used as the account which runs the program. If ramona is not running as root, this option has no effect.
- 'directory' option
- 'umask' option

Windows
-------
- working on Windows (based on pyev / libev?)
- daemonizing is not available on Windows - provide Windows Service option instead

Logging
-------
- Support for SIGHUP (reopen log files OR reset fully)
- log rotate of Ramona server log (stdout/stderr redirection)
- tail '-f' (forever) mode 
- compress older (xxxx.log.2+) log rotated files

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

Mailing to admin
----------------------
- Scan output streams of the program for keywords (by default 'error', 'fatal', 'exception') and send email when such event occurs
- On autorestart mail trigger
- On FATAL mail trigger
- Mailing issues to admin: https://github.com/ateska/ramona/issues/1

HTTP frontend
-------------
- Tail log
- Store static files in a way that setuptools and py2exe will work correctly. See: http://stackoverflow.com/questions/1395593/managing-resources-in-a-python-project
- (medium prio): Basic authentication
- (low prio): HTTPS

Deployment
----------
- Consider https://help.github.com/articles/splitting-a-subpath-out-into-a-new-repo for embedded deployments (for released versions)
