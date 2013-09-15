.. _nondaemon:

Nondaemonizing of Programs
==========================

Supervised programs should not daemonize_ themselves. Instead, they should run in the foreground.

You need to consult a specific program manual or help to find out how to disable its eventual daemonizing. You can check actual behaviour of a program by launching it from command-line (e.g. bash). The program should not detach from console, you basically need to press Ctrl-C to get back to shell prompt; in such a case, program is configured correctly for begin used with Ramona. Otherwise, if program detaches, you will be given by a shell prompt without any action needed, then program very likely has daemonized and it will not operated in Ramona properly.

Daemonizing of a program will basically break connection between Ramona and relevant program. Ramona will likely mark the program being in ``FATAL`` state (maybe even after several attempts to launch it) and certainly Ramona will not controll deamonized process (e.g. you will not be able to terminate it using Ramona tools).

.. _daemonize: http://en.wikipedia.org/wiki/Daemon_(computing)


Examples of Program Configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here are some "real world" program configuration examples:


MongoDB
+++++++
.. code-block:: ini

	[program:mongodb]
	command=/path/to/bin/mongod -f /path/to/mongodb.conf


RabbitMQ
++++++++
.. code-block:: ini

	[program:rabbitmq]
	command=/path/to/rabbitmq/bin/rabbitmq-server


Apache 2.x
++++++++++
.. code-block:: ini

   [program:apache2]
   command=/path/to/httpd -c "ErrorLog /dev/stdout" -DFOREGROUND


