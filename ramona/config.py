import os, sys, logging, re, platform, ConfigParser
###

L = logging.getLogger("config")

###

# Defaults are stated in documentation, if you change them here, update documentation too!
config_defaults = {
	'general' : {
		'appname' : 'ramona-driven-app',
		'logdir' : '<env>',
		'include' : '<siteconf>',
		'logmaxsize': '{0}'.format(512*1024*1024), # 512Mb
		'logbackups': '3',
		'logcompress': '1'
	},
	'ramona:server' : {
		'consoleuri': 'unix://.ramona.sock',
		'consoleuri@windows': 'tcp://localhost:7788',
		'pidfile': '',
		'log': '<logdir>',
		'loglevel': 'INFO',
	},
	'ramona:console' : {
		'serveruri': 'unix://.ramona.sock',
		'serveruri@windows': 'tcp://localhost:7788',
		'history': '',
	},
	'ramona:notify' : {
		'delivery': '',
		'sender': '<user>',
		'dailyat': '09:00'
	},
	'ramona:httpfend': {
		'listenaddr': "tcp://localhost:5588",
	}
	
}

###

config = ConfigParser.SafeConfigParser()
config.optionxform = str # Disable default 'lowecasing' behavior of ConfigParser
config_files = []
config_includes = []

config_platform_selector = platform.system().lower()

###

def read_config(configs=None, use_env=True):
	global config
	assert len(config.sections()) == 0

	# Prepare platform selector regex
	psrg = re.compile('^(.*)@(.*)$')

	# Load config_defaults
	psdefaults = []
	for section, items in config_defaults.iteritems():
		if not config.has_section(section):
			config.add_section(section)

		for key, val in items.iteritems():
		 	r = psrg.match(key)
		 	if r is None:
				config.set(section, key, val)
			else:
				if r.group(2) != config_platform_selector: continue
				psdefaults.append((section, r.group(1), val))

	# Handle platform selectors in config_defaults
	for section, key, val in psdefaults:
		config.set(section, key, val)


	# Load configuration files
	global config_files

	if configs is not None: configs = configs[:]
	else: configs = []
	if use_env:
		# Configs from environment variables
		config_envs = os.environ.get('RAMONA_CONFIG')
		if config_envs is not None:
			for config_file in config_envs.split(os.pathsep):
				configs.append(config_file)

	for cfile in configs:
		rfile = os.path.expanduser(cfile)
		if os.path.isfile(rfile):
			config_files.append(cfile)
		config.read([rfile])


	# Handle includes ...
	appname = config.get('general','appname')
	for _ in range(100):
		includes = config.get('general','include')
		if includes == '': break
		config.set('general','include','')
		includes = includes.split(';')
		for i in xrange(len(includes)-1,-1,-1):
			include = includes[i] = includes[i].strip()
			if include == '<siteconf>':
				# These are platform specific
				siteconfs = [
					'./site.conf',
					'./{}-site.conf'.format(appname),
					'/etc/{0}.conf'.format(appname),
					'~/.{0}.conf'.format(appname),
				]
				includes[i:i+1] = siteconfs
			elif include[:1] == '<':
				L.warning('Unknown include fragment: {0}'.format(include))
				continue

		for include in includes:
			rinclude = os.path.expanduser(include)
			if os.path.isfile(rinclude):
				config_includes.append(include)
				config.read([rinclude])

	else:
		raise RuntimeError("FATAL: It looks like we have loop in configuration includes!")

	# Threat platform selector alternatives
	if config_platform_selector is not None and config_platform_selector != '':
		for section in config.sections():
			for name, value in config.items(section):
		 		r = psrg.match(name)
		 		if r is None: continue
		 		if (r.group(2) != config_platform_selector): continue
		 		config.set(section, r.group(1), value)

	# Special treatment of some values
	if config.get('general', 'logdir') == '<env>':
		logdir = os.environ.get('LOGDIR')
		if logdir is None: logdir = os.curdir
		logdir = os.path.expanduser(logdir)
		config.set('general','logdir',logdir)
	elif config.get('general', 'logdir').strip()[:1] == '<':
		raise RuntimeError("FATAL: Unknown magic value in [general] logdir: '{}'".format(config.get('general', 'logdir')))

###

def get_boolean(value):
	'''
	Translates string/<any-type> value into boolean value. It is kind of similar to ConfigParser.getboolean but this one is used also in different places of code
	'''
	if value is True: return True
	if value is False: return False

	value = str(value)

	if value.upper() in ('TRUE','ON','YES','1'):
		return True
	elif value.upper() in ('FALSE','OFF','NO','0'):
		return False
	else:
		raise ValueError("Invalid boolean string '{0}'' (use one of true, on, yes, false, off or no).".format(value))

###

def get_numeric_loglevel(loglevelstring):
	'''
	Translates log level given in string into numeric value.
	'''
	numeric_level = getattr(logging, loglevelstring.upper(), None)
	if not isinstance(numeric_level, int): raise ValueError('Invalid log level: {0}'.format(loglevelstring))
	return numeric_level
