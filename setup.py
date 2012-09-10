from distutils.core import setup

# See http://guide.python-distribute.org/
# See http://docs.python.org/distutils/setupscript.html

setup(
	name='ramona',
	description='Enterprise-grade runtime supervisor',
	author='Ales Teska',
	author_email='ales.teska+ramona@gmail.com',
	version='0.2.dev2', # Also in ramona.__init__.py
	packages=['ramona'],
	license='BSD 2-clause "Simplified" License',
	long_description=open('README').read(),
	url='https://github.com/ateska/ramona',
	requires="pyev",
	classifiers=[
		'Development Status :: 3 - Alpha',
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

