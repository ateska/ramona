Tools Cookbook
==============

.. [TODO]: Example of init.d script (and modern alternatives like init) for ramona-based app

.. [TODO]: Using Ramona to execute unit tests


.. _smtp-configs:

SMTP configurations
-------------------

Here is a list of common SMTP configurations usable with Ramona email notification delivery subsystem (see :attr:`delivery` in [ramona:notify] configuration section).


GMail
`````
GMail from Google.

  .. code-block:: ini

    [ramona:notify]
    delivery=smtp://[user@gmail.com]:[password]@smtp.gmail.com:587/?tls=1

Credentials 'user' and 'password' need to be valid Google GMail account.

Example:

  .. code-block:: ini

    [ramona:notify]
    delivery=smtp://joe.doe@gmail.com:password123@smtp.gmail.com:587/?tls=1


Mandrill
````````
Transactional Email from MailChimp.

  .. code-block:: ini

    [ramona:notify]
    delivery=smtp://[user]:[API key]@smtp.mandrillapp.com:587


Credentials are from "SMTP & API Credentials" section in Mandrill settings.
User is "SMTP Username" respectively your account name at Mandrill.

API key can be created and obtained from this page in Mandrill settings too, if you don't have any, you can create one by pressing 'New API key' button. 

Example:

  .. code-block:: ini

    [ramona:notify]
    delivery=smtp://joe.doe@example.com:WJWZcoAaEQjggzVG1Y@smtp.mandrillapp.com:587

.. note:: 

  It seems that Mandrill is somehow sensitive to :attr:`sender` configuration; if it is not properly formulated, Mandill silently ignores an email.


Windows service control
-----------------------

Few generic advices how to manage Windows service manually.
Ramona system provides :ref:`cmdline-wininstall` and :ref:`cmdline-winuninstall` that are equivalents but generic way can sometimes become handy.

To start service:

.. code-block:: bash

  $ net start <service-name>


To stop service:

.. code-block:: bash

  $ net stop <service-name>


To uninstall service:

.. code-block:: bash

  $ sc delete <service-name>
