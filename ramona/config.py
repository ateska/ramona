import os, sys, ConfigParser
###

config_defaults = {
	'general' : {
		'logdir': '<none>',
	},
	'ramona:server' : {
		'svrname': 'ramona',
		'consoleuri': 'tcp://localhost:9876',
		'pidfile': '',
		'log': '<logdir>',
	},
	'ramona:console' : {
		'serveruri': 'tcp://localhost:9876',
		'history': '',
	},
	'ramona:smtp' : {
		'smtphost': '',
		'smtpport': '25',
		'sender': '',
	}
}

###

config = ConfigParser.SafeConfigParser()
config_files = []

###

def read_config(configs, use_env=True):
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


	if len(configs) == 0: 	
		# Use platform defaults
		configs = [
			os.path.splitext(sys.argv[0])[0] + '.conf',
			os.path.join('/', 'etc', os.path.basename(os.path.splitext(sys.argv[0])[0] + '.conf'))
		]

	for cfile in  configs:
		if os.path.isfile(cfile):
			config_files.append(cfile)
	
	config.read(config_files)

	# Special treatment of some values
	if config.get('general', 'logdir') == '<none>':
		logdir = os.environ.get('LOGDIR')
		if logdir is None: logdir = '.'
		config.set('general','logdir',logdir)
