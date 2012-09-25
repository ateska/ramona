
Features
========

HTTP Frontend
-------------
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
  # IP address/hostname where the HTTP frontend should listen
  host=127.0.0.1
  # Port where the HTTP frontend should listen
  port=5588
  # Use username and password options only if you want to enable basic authentication
  username=admin
  # Can get either plain text or a SHA1 hash, if the password starts with {SHA} prefix
  password=pass
  # SHA example. To generate use for example: echo -n "secret" | sha1sum
  #password={SHA}e5e9fa1ba31ecd1ae84f75caaa474f3a663f05f4
