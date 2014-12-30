
class AntDataPoint(object):
	def __init__(self, devtype, timestamp, payload):
		self.devtype = devtype
		self.timestamp = timestamp
		self.raw_payload = payload

	def __str__(self):
		return '%f %s %s' % (self.timestamp, self.devtype, repr(self.raw_payload))

	def event_timers(self):
		"A list of any nested event_timer objects"
		return []

