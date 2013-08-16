start (command-line)
====================

Start supervised program(s).

If Ramona server is not running, initiate also its start (optionally).

.. code-block:: bash

  <console.py> start [-h] [-n] [-i] [-f] [-S] [program [program ...]]


.. describe:: program

  Optionally specify program(s) in scope of the command. If none is given, all programs are considered in scope.


.. cmdoption:: start -n
               start --no-server-start

  Avoid eventual automatic start of Ramona server.


.. cmdoption:: start -i
               start --immediate-return

  Don't wait for start of programs and exit ASAP.


.. cmdoption:: start -f
               start --force-start

  Force start of programs even if they are in FATAL state.


.. cmdoption:: start -S
               start --server-only

  Start only server, programs are not started.
