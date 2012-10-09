import smtplib, logging, getpass, socket, os
from email.mime.text import MIMEText
from .config import config
###

L = logging.getLogger('sendmail')

###

def send_mail(recipient, subject, mail_body):

	smtp_host = config.get('ramona:smtp','host')
	if smtp_host == '':
		L.error('Cannot send mail - SMTP server is not configured.')
		return

	sender = config.get('ramona:smtp','sender')
	if sender is None: sender = get_default_fromaddr()

	msg = MIMEText(mail_body)
	msg['Subject'] = subject
	msg['From'] = sender
	msg['To'] = recipient

	s = smtplib.SMTP( config.getint('ramona:smtp','port'))
	s.sendmail(sender, [recipient], msg.as_string())
	s.quit()


def get_default_fromaddr():
	return "{0}@{1}".format(getpass.getuser(), socket.getfqdn())
