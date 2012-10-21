
Features
========

Program
-------

TODO
Program life cycle (statuses)


Program roaster
---------------

TODO


Command-line console
--------------------

TODO


Logging
-------

TODO


Mailing to admin
----------------

TODO


Custom tools
------------

TODO


Log scanning
------------

TODO


Ramona environment variables
----------------------------

TODO

.. attribute:: RAMONA_CONFIG

  TODO

  Separator is ';'


.. attribute:: RAMONA_SECTION

  TODO


HTTP front end (Web console)
----------------------------

.. image:: img/httpfend.png
   :width: 600px

- standalone process
- displays states of programs 
- allows to start/stop/restart each or all of them
- allows displaying tail of log files in "follow" mode 
- basic authentication

Configuration:

- The HTTP frontend is added to configuration file as any other program, only with the special option `command=<httpfend>`.
- To enable HTTP frontend, just add the below sample configuration and then open http://localhost:5588

.. code-block:: ini
  
  [program:ramonahttpfend]
  command=<httpfend>

For all configuration options see :ref:`config-ramonahttpfend`.