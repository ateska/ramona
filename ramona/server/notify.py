import os, datetime, socket, logging, time, pickle
import pyev
from ..config import config
from ..sendmail import send_mail

#

L = logging.getLogger('notify')

#

class stash(object):
	# Example structure of self.data dict is:
	# {
	#   "foo@bar.com": [] # List of lines to be included in the mail
	#   "bar@foo.com": ['notify1', 'notify2']
	# }


	def __init__(self, name):
		self.data = dict()
		self.name = name
		stashdir = config.get('ramona:notify', 'stashdir')
		if stashdir == '<none>':
			self.fname = None
		else:
			self.fname = os.path.join(stashdir, name)
			if os.path.isfile(self.fname):
				try:
					with open(self.fname, "rb") as f:
						self.data = pickle.load(f)
				except:
					L.warning("Ignored issue when loading stash file '{}'".format(self.fname))

		self.store_needed = False
		


	def add(self, recipients, ntfbody):
		 #TODO: Consider adding also ntfsubj (subject)
		for recipient in recipients:
			if not self.data.has_key(recipient):
				self.data[recipient] = list()
			self.data[recipient].append(ntfbody)

		self.store_needed = True


	def yield_text(self):
		for recipient, ntftexts in self.data.iteritems():
			textssend = []
			while True:
				try:
					textssend.append(ntftexts.pop())
				except IndexError:
					break

			yield recipient, textssend
		self.store_needed = True


	def store(self):
		if not self.store_needed: return
		self.store_needed = False
		if self.fname is None: return

		with open(self.fname, "wb") as f:
			pickle.dump(self.data, f)

		L.debug("Stash '{}' persisted!".format(self.name))

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
		
		self.stashes = {
			'daily': stash('daily'),
		}
		if self.delivery is not None:
			svrapp.watchers.append(pyev.Periodic(self.__get_daily_time_offset(), 24*3600, svrapp.loop, self.send_daily))

		#TODO: <sendmail> - see http://stackoverflow.com/questions/73781/sending-mail-via-sendmail-from-python
		#TODO: cmd:custom.sh


	def on_tick(self, now):
		for stash in self.stashes.itervalues():
			stash.store()


	def __get_daily_time_offset(self):
		sendtimestr = config.get("ramona:notify", "dailyat")
		
		# TODO: Enhance to better handle situation for the day when the timezone changes (switch from/to daylight saving time)
		sendtime = datetime.datetime.strptime(sendtimestr, "%H:%M").time()
		is_dst = time.daylight and time.localtime().tm_isdst > 0
		utc_offset = time.altzone if is_dst else time.timezone
		
		sendtimeseconds = sendtime.hour * 3600 + sendtime.minute * 60 + utc_offset
		
		if sendtimeseconds < 0:
			sendtimeseconds += 24*3600
		if sendtimeseconds >= 24*3600:
			sendtimeseconds -= 24*3600
		
		return sendtimeseconds
	
	
	def send_daily(self, watcher, revents):
		if watcher is not None:
			watcher.offset = self.__get_daily_time_offset()
			watcher.reset()

		appname = config.get('general','appname')
		hostname = socket.gethostname()
		subj = '{0} / {1} - daily'.format(appname, hostname)
		sep = '\n'+'-'*50+'\n'

		for recipient, textssend in self.stashes['daily'].yield_text():
			# Use pop to get the items from the stash to ensure that items that are put on the stash
			# during sending are not sent twice (in the current email and in the next email)
			if len(textssend) == 0: continue
			self._send_mail(subj, sep.join(textssend)+'\n', [recipient])


	def publish(self, target, ntfbody, ntfsubj):
		if ntfsubj is None: ntfsubj = 'notification'

		targettime, _, recipientconf = target.partition(":")
		recipientconf = recipientconf.strip()
		if recipientconf != "":
			recipients = [recipientconf]
		else:
			if self.delivery is None:
				L.warning("No default delivery set for notifications.")
				return
			recipients = self.delivery.receiver

		if targettime == "now":
			self._send_mail(
				ntfsubj, 
				ntfbody,
				recipients
			)

		elif targettime == "daily":
			self.stashes['daily'].add(recipients, ntfbody)
			
		else:
			L.warn("Target {} not implemented!".format(targettime))
			


	def _send_mail(self, subject, text, recipients):
		'''
		@param subject: Subject of the email message
		@param text: Text to be sent (it is prefixed with greeting and signature by this method)
		@param recipients: List of message recipients
		'''

		L.info("Sending '{}' mail to {}".format(subject, ', '.join(recipients)))

		fqdn = socket.getfqdn()
		appname = config.get('general','appname')
		hostname = socket.gethostname()

		subject = '{0} / {1} / {2} (by Ramona)'.format(appname, hostname, subject)

		sysident = 'Application: {0}\n'.format(appname)
		if hostname != fqdn and fqdn != 'localhost':
			sysident += 'Hostname: {0} / {1}'.format(hostname, fqdn)
		else:
			sysident += 'Hostname: {0}'.format(hostname)

		try:
			text = ''.join([
				'Hello,\n\nRamona produced following notification:\n\n', text,
				'\n\nSystem info:\n', sysident, #Two enters in the begging are intentional; arg 'text' should not have one at its end
				'\n\nBest regards,\nYour Ramona\n\nhttp://ateska.github.com/ramona\n'
			])
			
			self.delivery.send(recipients, subject, text)

		except:
			L.exception('Exception during sending mail - ignoring')
