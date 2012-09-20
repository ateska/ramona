from ..config import config

#

class notificator(object):


	def __init__(self, svrapp):
		self.appname = config.get('general','appname')


	def publish(self, target, prog_ident, stream_name, pattern, tail):

		nfttext = 'Hello,\nRamona detected following condition:\n'
		nfttext += 'Application: {0}\n'.format(self.appname)
		nfttext += 'Program: {0}\n'.format(prog_ident)
		nfttext += 'Pattern: {0}\n'.format(pattern)
		nfttext += '\n'
		nfttext += tail
		nfttext += '\nBest regards,\nYour Ramona\n'

		print nfttext
