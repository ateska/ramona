who (command-line)
==================

Show *who* is connected to the Ramona server.

Ramona server allows multiple clients to be connected at the same time. This command allows users to check who is connected to given Ramona server.

.. code-block:: bash

  <console.py> who [-h]


Output example:
::

	Connected clients:
	*UNIX /tmp/ramona-dev.sock @ 21-08-2013 19:49:10
	  TCP 127.0.0.1:53211 @ 21-08-2013 19:55:22
	  TCP [::1]:53211 @ 21-08-2013 18:35:16
