
class AntDataPoint(object):
	def __init__(self, timestamp, devspec, payload, prev_dp=None):
		self.timestamp = timestamp
		self.devspec = devspec
		self.raw_payload = payload

		# Subclasses that incorperate EventTimerSample objects should store
		# them as values in the "ets" dict. This allows code to operate on
		# all of the EventTimerSamples within an AntDataPoint object
		# independent of its device type subclass.
		self.ets = dict()

		self.subclass_init(prev_dp)

	def subclass_init(self, prev_dp):
		pass

	def __str__(self):
		s = '%f %s %s' % (self.timestamp, self.devspec, repr(self.raw_payload))
		timers = ", ".join(["timer[%s]={%s}" % (t,self.ets[t]) for t in sorted(self.ets.keys())])
		if len(timers):
			s += " " + timers
		return s
