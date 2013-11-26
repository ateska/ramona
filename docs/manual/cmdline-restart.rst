restart (command-line)
======================

Restart supervised program(s)


.. code-block:: bash

  <console.py> restart [-h] [-n] [-i] [-f] [program [program ...]]


.. describe:: program

  Optionally specify program(s) in scope of the command. If none is given, all programs are considered in scope.


.. cmdoption:: restart -n
               restart --no-server-start

  Avoid eventual automatic Ramona server start.
  This is relevant in case command ``restart`` is issued when Ramona server is not running.


.. cmdoption:: restart -i
               restart --immediate-return

  Don't wait for restart of programs and return ASAP.


.. cmdoption:: restart -f
               restart --force-start

  Force restart of programs even if they are in FATAL state.

  .. note::
	On UNIX systems, you can simulate ``restart -f`` command using ``HUP`` signal
	(e.g. ``kill -HUP [pid-of-ramona]`` from shell).
