
class AntDataPoint(object):
	def __init__(self, timestamp, payload, prev_dp=None):
		self.timestamp = timestamp
		self.raw_payload = payload

	def __str__(self):
		return '%f %s' % (self.timestamp, repr(self.raw_payload))

	def event_timers(self):
		"A list of any nested event_timer objects"
		return []

