.. _cmdline-wininstall:

wininstall (command-line)
=========================

**Windows only !**

Install the Ramona server as a Windows Service.

An user application will be able to run as Windows Service using this Ramona feature.
For more details, see :ref:`features-windowsservice`.


.. code-block:: bash

  <console.py> wininstall [-h] [-d] [-S] [program [program ...]]


.. describe:: program

  Optionally specify program(s) in scope of the command. If none is given, all programs are considered in scope.
  Programs in scope will be started when this Ramona Windows Service is started by OS.


.. cmdoption:: wininstall -S
               wininstall --server-only

  When service is acticated start only the Ramona server, not supervised programs.


.. cmdoption:: wininstall -d
               wininstall --dont-start

  Don't start Windows service (Ramona server) after an installation.
