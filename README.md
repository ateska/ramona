ramona
======

Your very own built-in supervisor component.

Ramona is a client/server system that allows to control and monitor project processes during runtime.
It is heavily influenced by supervisord but this is actually written from scratch (due to different initial requirement set).

It is primarily meant to be blended into your project source code set to provide supervisor/console functionality like start/stop control (init.d like), task frontend (e.g. unit/functional/performance test launcher) and other command-line oriented features. It should ideally represent the only executable of the project - kind of 'dispatcher' to rest of a project.

It is implemented in Python but it is not limited to be used only in Python projects.
Target platforms are all modern UNIXes, BSD derivates and Windows.
