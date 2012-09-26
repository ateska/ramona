
Features
========

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

RAMONA_CONFIGS
RAMONA_SECTION

TODO



HTTP front end (Web console)
----------------------------

.. image:: img/httpfend.png
   :width: 600px

- standalone process
- displays states of programs 
- allows to start/stop/restart each or all of them
- allows displaying tail of log files 
- basic authentication

Configuration:

- The HTTP frontend is added to configuration file as any other program, only with the special `command=<httpfend>`.
- Configuration sample including comments:

.. code-block:: ini
  
  [program:ramonahttpfend]
  command=<httpfend>
