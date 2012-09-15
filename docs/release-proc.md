Release procedure
=================

1. Make sure master branch (or relevant originating branch) is stable and releasable
2. Formulate release version 'string' (e.g. 0.9b1) -> use it instead placeholder [VERSION] bellow
3. git checkout -b release-[VERSION] master
4. Now we are working in the release branch
5. Check `./setup.py`:
	- version info
	- classifiers (e.g. Development Status)
6. Check `./ramona/__init__.py`:
	- version info
7. Check briefly `./README.md` and `./README`
8. Run tests:
	- `./ramona-dev.py unittests`
	- Functional test:
		- `./demo.py start`
		- `./demo.py status`
		- `./demo.py stop`
9. Run upload to testpypi.python.org: `./ramona-dev.py upload_test`
10. Check on http://testpypi.python.org/pypi/ramona
11. Prepare for final release !
12. Run upload to pypi.python.org: `./ramona-dev.py upload`
13. Check on http://pypi.python.org/pypi/ramona
14. Switch back to 'master' branch and enter [VERSION]dev1 into `./setup.py` and `./ramona/__init__.py`
