Release procedure
=================

1) Make sure master branch (or relevant originating branch) is stable and releasable
2) Formulate release version 'string' (e.g. 0.9b1) -> use it instead placeholder [VERSION] bellow
3) git checkout -b release-[VERSION] master
4) Now we are working in the release branch
5) Check ./setup.py:
	- version info
	- classifiers (e.g. Development Status)
6) Check ./__init__.py:
	- version info
7) Check briefly ./README.md and ./README
8) Run tests:
	- ./ramona-dev.py unittests
	- Functional test:
		- ./demo.py start
		- ./demo.py status
		- ./demo.py stop
