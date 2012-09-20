import smtplib, urlparse, logging, socket, getpass
from email.mime.text import MIMEText
from ..config import config

#

L = logging.getLogger('notify')

#

class notificator(object):


	def __init__(self, svrapp):
		self.appname = config.get('general','appname')

		delivery = config.get('ramona:notify','delivery').strip()
		if delivery == '':
			self.delivery = None
		else:
			delurl = urlparse.urlparse(delivery)
			if delurl.scheme == 'smtp':
				if delurl.hostname is None:
					L.error("Delivery URL has no hostname: {0}".format(delivery))
					self.delivery = None
				else:
					self.delivery = delurl
					try:# Connection test
						smtpcon = smtplib.SMTP(self.delivery.hostname, self.delivery.port)
						smtpcon.quit()
					except Exception, e:
						L.warning("Given SMTP server ({1}) is not responding: {0}".format(e, delivery))

					self.sender = config.get('ramona:notify','sender')
					if self.sender == '<user>':
						self.sender = '{0}@{1}'.format(getpass.getuser(), socket.gethostname())
					elif self.sender[:1] == '<':
						L.error('Invalid sender option: {0}'.format(self.sender))
						self.delivery = None

					self.receiver = config.get('ramona:notify', 'receiver').split(',')

		#TODO: <sendmail> - see http://stackoverflow.com/questions/73781/sending-mail-via-sendmail-from-python
		#TODO: cmd:custom.sh


	def publish(self, target, prog_ident, stream_name, pattern, tail):

		hostname = socket.gethostname()

		nfttext = 'Application: {0}\n'.format(self.appname)
		nfttext += 'Program: {0}\n'.format(prog_ident)
		nfttext += 'Pattern: {0}\n'.format(pattern)
		nfttext += 'Hostname: {0}\n'.format(hostname)
		nfttext += '\n'+'-'*80+'\n'
		nfttext += tail	
		nfttext += '\n'+'-'*80+'\n'

		#TODO: Decide what to do based on 'target' value

		self._send_mail('{0} / {1} / {2} / {3}'.format(
			self.appname,
			prog_ident,
			pattern,
			hostname,
			), nfttext)


	def _send_mail(self, subject, text):
		try:
			text = ''.join([
				'Hello,\n\nRamona detected following condition:\n',
				text,
				'\nBest regards,\nYour Ramona\n\nhttp://ateska.github.com/ramona\n'
			])

			sender = self.sender
			receiver = self.receiver

			msg = MIMEText(text, 'plain', 'utf-8')
			msg['Subject'] = subject + ' by Ramona'
			msg['From'] = sender
			msg['To'] = ', '.join(receiver)

			s = smtplib.SMTP(self.delivery.hostname, self.delivery.port)
			s.sendmail(sender, receiver, msg.as_string())
			s.quit()

		except:
			L.exception('Exception during sending mail - ignoring')
