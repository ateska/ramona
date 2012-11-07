import urlparse, socket, logging, socket
from ..config import config
from ..sendmail import send_mail

#

L = logging.getLogger('notify')

#

class notificator(object):

	def __init__(self, svrapp):
		delivery = config.get('ramona:notify','delivery').strip()
		if delivery == '':
			self.delivery = None
		else:
			try:
				self.delivery = send_mail(delivery)
			except RuntimeError, e:
				L.error("{0}".format(e))
				self.delivery = None

			if delivery is not None:
				self.delivery.connection_test()


		#TODO: <sendmail> - see http://stackoverflow.com/questions/73781/sending-mail-via-sendmail-from-python
		#TODO: cmd:custom.sh


	def publish(self, target, prog_ident, stream_name, pattern, tail):

		appname = config.get('general','appname')
		hostname = socket.gethostname()
		fqdn = socket.getfqdn()

		nfttext = 'Application: {0}\n'.format(appname)
		nfttext += 'Program: {0}\n'.format(prog_ident)
		nfttext += 'Pattern: {0}\n'.format(pattern)
		if hostname != fqdn :
			nfttext += 'Hostname: {0} / {1}\n'.format(hostname, fqdn)
		else:
			nfttext += 'Hostname: {0}\n'.format(hostname)
		nfttext += '\n'+'-'*50+'\n'
		nfttext += tail	
		nfttext += '\n'+'-'*50+'\n'

		if target.startswith('mailto'):
			recipient = urlparse.urlparse(target).path
		else: 
			recipient = None

		#TODO: Decide what to do based on 'target' value

		self._send_mail('{0} / {1} / {2} / {3}'.format(
				appname,
				prog_ident,
				pattern,
				hostname,
				), 
			nfttext,
			recipient
		)


	def _send_mail(self, subject, text, recipient=None):
		try:
			text = ''.join([
				'Hello,\n\nRamona detected following condition:\n',
				text,
				'\nBest regards,\nYour Ramona\n\nhttp://ateska.github.com/ramona\n'
			])

			if recipient is None:
				recipient = self.recipient
			elif isinstance(recipient, basestring):
				recipient = [recipient]

			self.delivery.send_mail(recipient, subject, text)

		except:
			L.exception('Exception during sending mail - ignoring')
