
Features
========

Program
-------

TODO
Program life cycle (statuses)


Program roaster
---------------

TODO


Command-line console
--------------------

TODO


Logging
-------

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


Log scanning
------------

TODO


Ramona environment variables
----------------------------

TODO

.. attribute:: RAMONA_CONFIG

  TODO

  Separator is ';'


.. attribute:: RAMONA_SECTION

  TODO


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
