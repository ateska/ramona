tail (command-line)
===================

Display the last part of a log (standard output and/or standard error) of specified program.

.. code-block:: bash

  <console.py> tail [-h] [-l {stdout,stderr}] [-f] [-n N] program


.. describe:: program

  Specify the program in scope of the command.


.. cmdoption:: tail -l {stdout,stderr}
               tail --log-stream {stdout,stderr}

  Specify which standard stream to use.
  Default is ``stderr``.


.. cmdoption:: tail -f
               tail --follow

  Causes tail command to not stop when end of stream is reached, but rather to wait for additional data to be appended to the input.


.. cmdoption:: tail -n N
               tail --lines N

  Output the last N lines, instead of the last 40.

