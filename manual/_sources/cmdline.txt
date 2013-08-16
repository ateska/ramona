Command line console
====================

Command-line console is a basic tool for interaction with Ramona-equipped application.

User can issue commands to Ramona server thru this tool or execute any of custom tools.


Generic options
---------------

Generic options should be given prior actual command on the command line.

.. cmdoption:: -c CONFIGFILE
               --config CONFIGFILE

  Specify configuration file(s) to read (this option can be given more times). This will override build-in application-level configuration.


.. cmdoption:: -h
               --help

  Displays build-in help.


.. cmdoption:: -d
               --debug

  Enable debug (verbose) output.


.. cmdoption:: -s
               --silent

  Enable silent mode of operation (only errors are printed).


Common commands
---------------

.. toctree::
   cmdline-start.rst
   cmdline-stop.rst
   cmdline-restart.rst
   cmdline-status.rst
   cmdline-tail.rst
   cmdline-console.rst
   cmdline-server.rst
   cmdline-wininstall.rst
   cmdline-winuninstall.rst
