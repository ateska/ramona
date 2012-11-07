import urlparse, smtplib, logging, getpass, socket, os
from email.mime.text import MIMEText
from .config import config
###

L = logging.getLogger('sendmail')

###

# Configure urlparse
if 'smtp' not in urlparse.uses_params: urlparse.uses_params.append('smtp')

###

class send_mail(object):

	def __init__(self, deliveryuri, sender=None):
		delurl = urlparse.urlparse(deliveryuri)
		if delurl.scheme == 'smtp' :
			if delurl.hostname is None:
				raise RuntimeError("Delivery URL has no hostname: {0}".format(delivery))
			else:
				self.hostname = delurl.hostname
				self.port = delurl.port if delurl.port is not None else 25
				self.username = delurl.username
				self.password = delurl.password
				self.params = dict(urlparse.parse_qsl(delurl.params))

				if sender is None:
					self.sender = config.get('ramona:notify','sender')
				else:
					self.sender = sender

				if self.sender == '<user>':
					self.sender = self.get_default_fromaddr()
				elif self.sender[:1] == '<':
					raise RuntimeError('Invalid sender option: {0}'.format(self.sender))

				self.receiver = config.get('ramona:notify', 'receiver').split(',')

		else:
			raise RuntimeError("Unknown delivery method in {0}".format(deliveryuri))


	def connection_test(self):
		try: # Connection test
			s = smtplib.SMTP(self.hostname, self.port)
			if self.params.get('tls', '1') == '1': s.starttls()
			if self.username is not None and self.password is not None:
				s.login(self.username, self.password)

			s.quit()
		except Exception, e:
			L.warning("Given SMTP server ({1}/{2}) is not responding: {0}".format(e, self.hostname, self.port))
			return False
		return True


	def send_mail(self, recipients, subject, mail_body, sender=None):

		if sender is None: sender = self.sender

		msg = MIMEText(mail_body, 'plain', 'utf-8')
		msg['Subject'] = subject + ' by Ramona'
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
		return "{0}@{1}".format(getpass.getuser(), socket.getfqdn())
