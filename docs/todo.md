TODO list
=========

Generic
-------
- split demo to demo&test (code that is more about testing and intentionally fails should not be in demo)
- exitcodes option for autorestart (autorestart=1,2,3)
- (low prio): SSL (optional) for protecting console-server channel
- ulimit/resources (similar to core dump) -> minfds, minprocs
- Unify & document sys.exit codes 
- Reload/reset command (restarting ramona server)
- Restart in yield mode should also terminate & start ramona server
- [tool:x] support (how to do this properly - config is read __after__ arguments are parsed)
- console command enable/disable to allow change status during runtime
- [program:x] disabled 'magic' options:
	 - e.g. <on-platform linux:mac>
- test Ramona how it runs in out-of-diskspace conditions
- 'user' option - If ramona runs as root, this UNIX user account will be used as the account which runs the program. If ramona is not running as root, this option has no effect.

Logging
-------
- Support for SIGHUP (reopen log files OR reset fully)
- log rotate of Ramona server log (stdout/stderr redirection)

Configuration
-------------
- environment variables expansion in configuration

Watchdog
--------
- watchdog functionality (child process is signaling that is alive periodically)
- watchdog for non-managed programs (e.g. [watchdog:apache]) + restart commands

Python specific
---------------
- native python program execution (using utils.get_python_exec - substitute for STRIGAPYTHON)
- python version (minimal) check

Mailing to admin
----------------
- On autorestart mail trigger
- On FATAL mail trigger
- Mailing issues to admin: https://github.com/ateska/ramona/issues/1
- Standalone log scanner (not connected to particular program) to enable supervising of e.g. CGI scripts
- daily/weekly/monthly targets

HTTP frontend
-------------
- Store static files in a way that py2exe will work correctly.
- RESTful API
- (low prio): HTTPS

Deployment
----------
- Consider https://help.github.com/articles/splitting-a-subpath-out-into-a-new-repo for embedded deployments (for released versions)
