#!/usr/bin/env python
import os, sys, fnmatch, shutil
import ramona

class RamonaDevConsoleApp(ramona.console_app):

	@ramona.tool
	def clean(self):
		'Clean project directory from intermediate files (*.pyc)'
		for root, dirnames, filenames in os.walk('.'):
			for filename in fnmatch.filter(filenames, '*.pyc'):
				filename = os.path.join(root, filename)
				if not os.path.isfile(filename): continue
				os.unlink(filename)

		try:
			shutil.rmtree('dist')
		except:
			pass

		try:
			shutil.rmtree('build')
		except:
			pass

		for f in ['MANIFEST', 'demo_history', 'ramonadev_history']:
			try:
				os.unlink(f)
			except:
				pass


	@ramona.tool
	def unittests(self):
		'Seek for all unit tests and execute them'
		import unittest
		tl = unittest.TestLoader()
		ts = tl.discover('.', '__utest__.py')

		tr = unittest.runner.TextTestRunner(verbosity=2)
		res = tr.run(ts)

		return 0 if res.wasSuccessful() else 1


	@ramona.tool
	def sdist(self):
		'Prepare distribution package'
		os.execl(sys.executable, sys.executable, 'setup.py', 'sdist', '--formats=gztar,zip', '--owner=root', '--group=root')


	@ramona.tool
	def upload_test(self):
		'Upload (register) new version to TestPyPi'
		os.system("{0} setup.py \
			sdist --formats=gztar,zip --owner=root --group=root \
			register -r http://testpypi.python.org/pypi \
			upload -r http://testpypi.python.org/pypi \
			".format(sys.executable)
		)

	@ramona.tool
	def upload_test(self):
		'Upload (register) new version to PyPi'
		os.system("{0} setup.py \
			sdist --formats=gztar,zip --owner=root --group=root \
			register -r http://pypi.python.org/pypi \
			upload -r http://pypi.python.org/pypi \
			".format(sys.executable)
		)

	@ramona.tool
	def version(self):
		print ramona.version


if __name__ == '__main__':
	app = RamonaDevConsoleApp(configuration='./ramona.conf')
	app.run()
