class kmp_search(object):
	'''Implementation of Knuth-Morris-Pratt string matching algorithm
	See http://en.wikipedia.org/wiki/Knuth-Morris-Pratt_algorithm for more details.

	Basically this is useful for searching pattern (string) in the non-persistent stream of data.
	'''

	def __init__(self, pattern):
		# allow indexing into pattern and protect against change during yield
		self.pattern = list(pattern)
		self.patternlen = len(self.pattern)

		# build table of shift amounts
		self.shifts = [1] * (self.patternlen + 1)
		shift = 1
		for pos in range(self.patternlen):
			while shift <= pos and self.pattern[pos] != self.pattern[pos-shift]:
				shift += self.shifts[pos-shift]
		self.shifts[pos+1] = shift

		self.startpos = 0
		self.matchsel = 0


	def search(self, text):
		for c in text:
			while self.matchsel == self.patternlen or self.matchsel >= 0 and self.pattern[self.matchsel] != c:
				self.startpos += self.shifts[self.matchsel]
				self.matchsel -= self.shifts[self.matchsel]
			self.matchsel += 1
			if self.matchsel == self.patternlen:
				return self.startpos
		return -1

