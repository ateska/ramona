
Introduction
============

Ramona is runtime supervisor: component of a software product that takes care of smooth start and stop of the solution (including daemonization), of it's runtime monitoring (logging, unexpected exits, etc.) and of various tasks that are connected with project like continuous integration, unit test automation, documentation builds etc.

Full set of features is described here_.

.. _here: features.html


Integration with your project
-----------------------------

Assuming you have successfully installed_ Ramona, you can start integrating it with your project.

.. _installed: install.html

You have to provide two files: **supervisor launcher** and its **configuration**.

Supervisor launcher
###################

Supervisor launcher is small piece of Python code, that is actually executable by user.

Assuming your project is called *foo*, you need to create file ``foo.py`` with following content (just copy&paste it).

.. code-block:: python

  #!/usr/bin/env python
  import ramona

  class FooConsoleApp(ramona.console_app):
	pass

  if __name__ == '__main__':
	app = FooConsoleApp(configuration='./foo.conf')
	app.run()

Make sure that it is marked as executable (e.g. by ``chmod a+x ./foo.py`` on UNIX platform).

.. note::

  It is important to use correct version of Python interpreter with Ramona. Some systems happens to have multiple versions installed, so PATH environment variable should be correctly set for relevant user(s) to point to proper Python.


Configuration
#############

You also need to create application-level configuration file which will instruct Ramona what to do.

Create file named ``foo.conf`` (actually referenced from ``foo.py`` you just created - you are free to change name based on your preferences).

Content of the file is as follows::

  [general]
  appname=foo

  [program:appserver]
  command=[command-to-start-your-app]


``[command-to-start-your-app]`` is command that your project uses to start.

You can entry ``[program:x]`` section more times - for each 'long running' component of your project.


Basic usage
-----------

Ramona provides build-in help system.

.. code-block:: bash

  $ ./foo.py --help
  usage: foo.py [-h] [-c CONFIGFILE] [-d] [-s]
                {start,stop,restart,status,help,tail,console,server} ...
  
  optional arguments:
    -h, --help            show this help message and exit
    -c CONFIGFILE, --config CONFIGFILE
                          Specify configuration file(s) to read (this option can
                          be given more times). This will override build-in
                          application level configuration.
    -d, --debug           Enable debug (verbose) output.
    -s, --silent          Enable silent mode of operation (only errors are
                          printed).
  
  subcommands:
    {start,stop,restart,status,help,tail,console,server}
      start               Launch subprocess(es)
      stop                Terminate subprocess(es)
      restart             Restart subprocess(es)
      status              Show status of subprocess(es)
      help                Display help
      tail                Tail log of specified program
      console             Enter interactive console mode
      server              Launch server in the foreground

Start of your application::

  $ ./foo.py start


Stop of your application::

  $ ./foo.py stop

