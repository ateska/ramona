.. _nondaemon:

Nondaemonizing of Programs
==========================

Supervised programs should not daemonize_ themselves. Instead, they should run in the foreground.

You need to consult the manual, the man page, or check other help resources to find out how to disable the eventual daemonizing of the program which you want to control with Ramona. You can check the actual behavior of a program by launching it from the command-line (e.g. bash). The program should not detach from the console, after launching the program you need to press Ctrl-C to get back to the shell prompt. In such a case, the program is configured correctly for being used with Ramona. Otherwise, if the program detaches, you will get a shell prompt without any further action, then program very likely has daemonized or send to the background and it will not operated with Ramona properly.

Daemonizing of a program will basically break the connection between Ramona and the relevant program. Ramona will likely mark the program being in ``FATAL`` state (maybe even after several attempts to launch it) and certainly Ramona will not control it as a deamonized process (e.g. you will not be able to terminate it using Ramona tools).

.. _daemonize: http://en.wikipedia.org/wiki/Daemon_(computing)


Examples of Program Configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this section you find some "real world" program configuration examples:


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

Lighttpd
++++++++
.. code-block:: ini

   [program:lighttpd]
   command=/path/to/lighttpd -D -f /path/to/lighttpd.conf
