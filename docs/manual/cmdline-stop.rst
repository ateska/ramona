.. _cmdline-stop:

stop (command-line)
===================

Stop supervised program(s).

Optionally also terminate Ramona server.
By default, the Ramona server will exit automatically after last supervised program terminates using the 'stop' command.

.. code-block:: bash

  <console.py> stop [-h] [-i] [-c] [-E] [-T] [program [program ...]]


.. describe:: program

  Optionally specify program(s) in scope of the command. If none is given, all programs are considered in scope.


.. cmdoption:: stop -i
               stop --immediate-return

  Dont wait for termination of programs and exit ASAP.


.. cmdoption:: stop -c
               stop --core-dump

  Stop program(s) to produce core dump (core dump must be enabled in program configuration). 
  It is archived by sending signal that lead to dumping of a core file.


.. cmdoption:: stop -E
               stop --stop-and-exit

  Stop all programs and exit Ramona server.
  This is a default behaviour of the ``stop`` command.


.. cmdoption:: stop -S
               stop --stop-and-stay

  Stop all programs but keep Ramona server running.
