server (command-line)
=====================

Start the Ramona server in the foreground.
You can use `Ctrl-C` to terminate server interactively. Also you will be able to see output of a Ramona server directly on a terminal.

.. code-block:: bash

  <console.py> server [-h] [-S] [program [program ...]]


.. describe:: program

  Optionally specify program(s) in scope of the command. If none is given, all programs are considered in scope.


.. cmdoption:: server -S
               server --server-only

  Start only Ramona server, programs are not launched.
