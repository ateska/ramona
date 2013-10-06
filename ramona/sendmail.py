import urlparse, smtplib, logging, getpass, socket, os, string
from email.mime.text import MIMEText
from .config import config
###

L = logging.getLogger('sendmail')

###

# Configure urlparse
if 'smtp' not in urlparse.uses_query: urlparse.uses_query.append('smtp')

###

class send_mail(object):

	def __init__(self, deliveryuri, sender=None):
		delurl = urlparse.urlparse(deliveryuri)
		if delurl.scheme == 'smtp' :
			if delurl.hostname is None:
				raise RuntimeError("Delivery URL '{0}' has no hostname".format(deliveryuri))
			else:
				self.hostname = delurl.hostname
				self.port = delurl.port if delurl.port is not None else 25
				self.username = delurl.username
				self.password = delurl.password
				self.params = dict(urlparse.parse_qsl(delurl.query))

				if sender is None:
					self.sender = config.get('ramona:notify','sender')
				else:
					self.sender = sender

				if self.sender == '<user>':
					self.sender = self.get_default_fromaddr()
				elif self.sender[:1] == '<':
					raise RuntimeError('Invalid sender option: {0}'.format(self.sender))

		else:
			raise RuntimeError("Unknown delivery method in {0}".format(deliveryuri))

		self.receiver = map(string.strip, config.get('ramona:notify', 'receiver').split(','))


	def send(self, recipients, subject, mail_body, sender=None):

		if sender is None: sender = self.sender

		msg = MIMEText(mail_body, 'plain', 'utf-8')
		msg['Subject'] = subject
		msg['From'] = sender
		msg['To'] = ', '.join(recipients)

		s = smtplib.SMTP(self.hostname, self.port)
		if self.params.get('tls', '1') == '1': s.starttls()
		if self.username is not None and self.password is not None:
			s.login(self.username, self.password)

		s.sendmail(sender, recipients, msg.as_string())
		s.quit()


	@staticmethod
	def get_default_fromaddr():
		hostname = socket.getfqdn()
		if hostname == 'localhost': hostname = socket.gethostname()
		return "{0}@{1}".format(getpass.getuser(), hostname)
