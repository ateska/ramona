import os, sys, logging, ConfigParser
###

config_defaults = {
	'general' : {
		'appname' : 'ramona-driven-app',
		'logdir' : '<none>',
		'include' : '<siteconf>',
		'logmaxsize': '{0}'.format(512*1024*1024), # 512Mb
		'logbackups': '3',
	},
	'ramona:server' : {
		'consoleuri': 'unix://.ramona.sock',
		'pidfile': '',
		'log': '<logdir>',
		'loglevel': 'INFO',
	},
	'ramona:console' : {
		'serveruri': 'unix://.ramona.sock',
		'history': '',
	},
	'ramona:notify' : {
		'delivery': '',
		'sender': '<user>',
	}
}

###

config = ConfigParser.SafeConfigParser()
config.optionxform = str # Disable default 'lowecasing' behavior of ConfigParser
config_files = []
config_includes = []

###

def read_config(configs=None, use_env=True):
	global config
	assert len(config.sections()) == 0

	# Load defaults
	for section, items in config_defaults.iteritems():
		if not config.has_section(section):
			config.add_section(section)

		for key, val in items.iteritems():
			config.set(section, key, val)


	# Load configuration files
	global config_files

	if configs is not None: configs = configs[:]
	else: configs = []
	if use_env:
		# Configs from environment variables
		config_envs = os.environ.get('RAMONA_CONFIG')
		if config_envs is not None:
			for config_file in config_envs.split(':'):
				configs.append(config_file)

	for cfile in  configs:
		if os.path.isfile(cfile):
			config_files.append(cfile)
		config.read([cfile])

	# Handle includes ...
	for _ in range(100):
		includes = config.get('general','include')
		if includes == '': break
		config.set('general','include','')
		includes = includes.split(':')
		for i in xrange(len(includes)-1,-1,-1):
			include = includes[i] = includes[i].strip()
			if include == '<siteconf>':
				# These are platform specific
				siteconfs = ['./site.conf', '/etc/{0}.conf'.format(config.get('general','appname'))]
				includes[i:i+1] = siteconfs
			elif include[:1] == '<':
				L.warning('Unknown include fragment: {0}'.format(include))
				continue

		for include in includes:
			if os.path.isfile(include):
				config_includes.append(include)
				config.read([include])

	else:
		raise RuntimeError("FATAL: It looks like we have loop in configuration includes!")

	# Special treatment of some values
	if config.get('general', 'logdir') == '<none>':
		logdir = os.environ.get('LOGDIR')
		if logdir is None: logdir = '.'
		logdir = os.path.expanduser(logdir)
		config.set('general','logdir',logdir)

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
