
Features
========

Execution model
---------------

TODO: Diagram of how Ramona operated (console, server, programs)


Program and program roaster
---------------------------

Ramona maintains pre-configured set of programs; these programs are placed in a 'roaster', list that is managed by Ramona server.
Each program in this roaster has a status that reflects its current phase of life cycle.

List of program statuses
^^^^^^^^^^^^^^^^^^^^^^^^
  * DISABLED - program is disabled by configuration; Ramona will not launch this program at any condition.
  * STOPPED - program is stopped (not running); you can launch it by 'start' command.
  * STARTING - program has been just launched.
  * RUNNING - program is running for some time already.
  * STOPPING - program has been asked to terminate but it has not exited yet.
  * FATAL - program exited in a errorneous way (maybe several times in row) and Ramona evaluated this as non-recoverable error.
  * CFGERROR - program is incorrectly configured and cannot be launched.


Command-line console
--------------------

Ramona provides command-line console, a tool that allows interaction with Ramona server and thru this controlling of all application programs. This tool can be tighly integrated with application that uses Ramona and it is designed to represent 'single point of execution' of given application.

This approach simplifies maintenance of the application and allow easy operating of even complex applications consisting of many different programs.

User can also add their custom commands (see `custom tools`_) to cover all needs of its application.


Logging and log scanning
------------------------

TODO


Mailing to admin
----------------

TODO


Custom tools
------------

TODO


Example of tool function:

.. code-block:: python

  class FooConsoleApp(ramona.console_app):

  	@ramona.tool
  	def mytool(self):
  		'''This is help text of my tool'''
  		...


Example of tool class:

.. code-block:: python

  class FooConsoleApp(ramona.console_app):

  	@ramona.tool
  	class mytool(object):
  		'''This is help text of my tool'''
  	
  		def init_parser(self, cnsapp, parser):
			parser.description = '...'
			parser.add_argument(...)
  
		def main(self, cnsapp, args):
  			...


Ramona environment variables
----------------------------

Ramona sets following environment variables to propagate certain information to programs, that are launched as Ramona subprocesses.
This allows exchange of configuration information in a control way, helping to keep overall configuration nice and tidy.

.. attribute:: RAMONA_CONFIG

  This environment variable specifies list of configuration files that has been used to configure Ramona server.
  List is ordered (configuration values can overlap so correct override behaviour needs to be maintained) and its separator is ':' for POSIX or ';' for Windows. See ``os.pathsep`` in Python.

  Client application can use this variable to read configuration from same place(s) as Ramona did.


.. attribute:: RAMONA_SECTION

  This environment variable reflect name of section in Ramona configuration files that in relevant for actual program (subprocess of Ramona). Uses can use this value to reach program specific configuration options.


Example:

  .. code-block:: ini

    [program:envdump]
    command=bash -c "echo RAMONA_CONFIG: ${RAMONA_CONFIG}; echo RAMONA_SECTION: ${RAMONA_SECTION}"


This produces following output:

  .. code-block:: console

    RAMONA_CONFIG: ./test.conf
    RAMONA_SECTION: program:envdump

.. note::

  Configuration files are compatible with Python Standart Library ``ConfigParser`` module.
  You can read configuration files using this module in order given by ``RAMONA_CONFIG`` environment variable and access configuration values. You can use ``RAMONA_SECTION`` environment variable to identify section in configuration files that is relevant to your actual program.


HTTP front end (Web console)
----------------------------

.. image:: img/httpfend.png
   :width: 600px

- standalone process
- displays states of programs 
- allows to start/stop/restart each or all of them
- allows displaying tail of log files in "follow" mode 
- basic authentication

Configuration:

- The HTTP frontend is added to configuration file as any other program, only with the special option `command=<httpfend>`.
- To enable HTTP frontend, just add the below sample configuration and then open http://localhost:5588

.. code-block:: ini
  
  [program:ramonahttpfend]
  command=<httpfend>

For all configuration options see :ref:`config-ramonahttpfend`.


Windows service
---------------

Ramona is using `Window Services`_ for background execution on Windows platform.
It also depends on ``pythonservice.exe`` tool from `Python for Windows extensions`_ package. Therefore it is possible to install Ramona equipped application as Windows Service via commands that are provided by Ramona system. This can be used for automatic start-up after system (re)boot or to enable smooth development on Windows machine.

For more details continue to:

- :ref:`cmdline-wininstall`
- :ref:`cmdline-winuninstall`

.. _`Window Services`: http://en.wikipedia.org/wiki/Windows_service
.. _`Python for Windows extensions`: http://sourceforge.net/projects/pywin32/
