Tools Cookbook
==============

.. [TODO]: Example of init.d script (and modern alternatives like init) for ramona-based app

.. [TODO]: Using Ramona to execute unit tests


Windows service manual control
------------------------------

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
