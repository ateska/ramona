import glob, os, sys
from distutils.core import Extension, setup
from distutils.command.build_ext import build_ext

########
# To enable development, run:
# python2.7 setup.py build_ext --inplace
#

# See http://guide.python-distribute.org/
# See http://docs.python.org/distutils/setupscript.html

ext_modules = []

###

def expand(*lst):
	result = []
	for item in lst:
		for name in sorted(glob.glob(item)):
			result.append(name)
	return result

###

class my_build_ext(build_ext):


	def build_extension(self, ext):
		if ext == CORE:
			self.build_libev(ext)

			ext.libraries.append('ev')
			ext.library_dirs.append(os.path.join(self.libev_inst, 'lib'))
			ext.include_dirs.append(os.path.join(self.libev_inst, 'include'))
			
			return build_ext.build_extension(self, ext)
		else:
			raise RuntimeError("Unknown extensiton to build: {}".format(ext))


	def build_libev(self, ext):
		self.libev_inst = os.path.join(os.path.abspath(self.build_temp), 'libev')

		if not os.path.exists(self.libev_inst):

			if not os.path.exists('libev/config.h'):
				ret = os.system('(cd libev && ./configure --enable-static --disable-shared --prefix={})'.format(self.libev_inst))
				if ret != 0: sys.exit(1)
			
			ret = os.system('(cd libev && make)')
			if ret != 0: sys.exit(1)
			
			ret = os.system('(cd libev && make install)')
			if ret != 0: sys.exit(1)

###

CORE = Extension(
	name='ramona.core',
	sources=[
		'ramona/core/module.c',
	],
	depends=expand('libev/*.*')
)

ext_modules.append(CORE)

###

setup(
	name='ramona',
	description='Enterprise-grade runtime supervisor',
	author='Ales Teska',
	author_email='ales.teska+ramona@gmail.com',
	version='master', # Also in ramona.__init__.py (+ relevant version format specification)
	packages=['ramona','ramona.server','ramona.console','ramona.console.cmd','ramona.httpfend'],
	license='BSD 2-clause "Simplified" License',
	long_description=open('README').read(),
	url='http://ateska.github.com/ramona/',
	download_url='http://pypi.python.org/pypi/ramona',
	zip_safe=True,
	package_data={
		'ramona.httpfend': [
			'*.html',
			'static/miniajax/*.js',
			'static/bootstrap/css/*.css',
			'static/img/*.gif',
			'static/img/*.ico',
			]
	},
	ext_modules=ext_modules,
	cmdclass=dict(build_ext=my_build_ext),
	classifiers=[
		'Development Status :: 4 - Beta',
		'Environment :: Console',
		'Intended Audience :: Developers',
		'Intended Audience :: Information Technology',
		'Intended Audience :: System Administrators',
		'License :: OSI Approved :: BSD License',
		'Natural Language :: English',
		'Operating System :: MacOS :: MacOS X',
		'Operating System :: Microsoft :: Windows',
		'Operating System :: POSIX',
		'Operating System :: Unix',
		'Programming Language :: Python :: 2.7',
		'Topic :: Software Development',
		'Topic :: System :: Monitoring',
		'Topic :: System :: Systems Administration',
	],
)
