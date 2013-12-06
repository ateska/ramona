#!/usr/bin/env python
#
# Released under the BSD license. See LICENSE.txt file for details.
#
import os
import sys
import fnmatch
import shutil
import ramona

class RamonaDevConsoleApp(ramona.console_app):

	@ramona.tool
	def clean(self):
		"""Clean project directory from intermediate files (*.pyc)"""
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
		"""Seek for all unit tests and execute them"""
		import unittest
		tl = unittest.TestLoader()
		ts = tl.discover('.', '__utest__.py')

		tr = unittest.runner.TextTestRunner(verbosity=2)
		res = tr.run(ts)

		return 0 if res.wasSuccessful() else 1

	@ramona.tool
	def sdist(self):
		"""Prepare the distribution package"""
		os.execl(sys.executable, sys.executable, 'setup.py', 'sdist', '--formats=gztar,zip', '--owner=root', '--group=root')

	@ramona.tool
	def upload_test(self):
		"""Upload (register) a new version to TestPyPi"""
		os.system("LC_ALL=en_US.UTF-8 {0} setup.py \
			sdist --formats=gztar,zip --owner=root --group=root \
			register -r http://testpypi.python.org/pypi \
			upload -r http://testpypi.python.org/pypi \
			".format(sys.executable)
		)

	@ramona.tool
	def upload(self):
		"""Upload (register) a new version to PyPi"""
		os.system("LC_ALL=en_US.UTF-8 {0} setup.py \
			sdist --formats=gztar,zip --owner=root --group=root \
			register -r http://pypi.python.org/pypi \
			upload -r http://pypi.python.org/pypi \
			".format(sys.executable)
		)

	@ramona.tool
	def version(self):
		"""Returns the Ramona version number"""
		print ramona.version

	@ramona.tool
	def manual(self):
		"""Build a HTML version of the manual"""
		if os.path.isdir('docs/manual/_build'):
			shutil.rmtree('docs/manual/_build')
		os.system('LC_ALL=en_US.UTF-8 make -C docs/manual html')

	@ramona.tool
	def gource(self):
		"""Creates visualizations about the Ramona development"""
		import subprocess, re

		cmd= r"""git log --pretty=format:user:%aN%n%ct --reverse --raw --encoding=UTF-8 --no-renames"""
		gitlog = subprocess.check_output(cmd, shell=True)

		gitlog = re.sub(r'\nuser:Ales Teska\n','\nuser:ateska\n',gitlog)
		gitlog = re.sub(r'\nuser:Jan Stastny\n','\nuser:jstastny\n',gitlog)

		cmd  = r"""gource -1280x720 --stop-at-end --highlight-users --seconds-per-day .5 --title "Ramona" --log-format git -o - -"""
		cmd += " | "
		cmd += r"ffmpeg -y -r 60 -f image2pipe -vcodec ppm -i - -vcodec libx264 -preset ultrafast -pix_fmt yuv420p -crf 16 -threads 0 -bf 0 gource.mp4"

		x = subprocess.Popen(cmd, stdin=subprocess.PIPE, shell=True)
		x.communicate(gitlog)

if __name__ == '__main__':
	app = RamonaDevConsoleApp(configuration='./ramona.conf')
	app.run()
