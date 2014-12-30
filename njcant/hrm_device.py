
from njcant.event_timer import AntEventTimerSpec, AntEventTimerSample
from njcant.device_baseclass import AntDataPoint

hrm_beat_ets_spec = AntEventTimerSpec(
	event_desc       = 'beat',
	ticks_per_sec    = 1024.0,
	event_count_wrap = 256,
	clock_wrap       = 256*256,
)

class HrmDataPoint(AntDataPoint):
	def __init__(self, timestamp, payload, prev_dp):
		AntDataPoint.__init__(self, 'HRM', timestamp, payload)

		self.raw_last_beat = payload[4] + 256*payload[5]
		self.raw_beat_count = payload[6]
		self.raw_hr = payload[7]

		# Not sure of the format, but from observation of my garmin HRM payload[2:4] is always previous beat time so long as payload[0] (which appears to be flags) doesn't have bit 0 set and payload[1] is 0.  In some messages payload[0:4] is used to convey some other data which I don't know how to interpret.
		if payload[0] & 1 == 0 and payload[1] == 0:
			self.raw_prev_beat = payload[2] + 256*payload[3]
		else:
			self.raw_prev_beat = None

		prev_beat_ets = None if prev_dp is None else prev_dp.beat_ets
		self.beat_ets = AntEventTimerSample(hrm_beat_ets_spec, self.raw_beat_count, self.raw_last_beat, prev_beat_ets)
		
	def __str__(self):
		s = AntDataPoint.__str__(self) + " hr=%d beats={%s}" % (self.raw_hr, str(self.beat_ets))
		if self.raw_prev_beat is not None:
			s += " prevat=%d" % self.raw_prev_beat
		return s

	def event_timers(self):
		return [self.beat_ets]

	def prev_beat_realtime(self):
		"The real time of the beat before last, if available"
		if self.beat_ets.last_at_realtime is None or self.raw_prev_beat is None:
			return None

		prevlast_diff_ticks = self.raw_last_beat - self.raw_prev_beat
		if prevlast_diff_ticks < 0:
			# clock wrap between previous and last beat
			prevlast_diff_ticks += hrm_beat_ets_spec.clock_wrap

		prevlast_diff_secs = prevlast_diff_ticks / hrm_beat_ets_spec.ticks_per_sec

		return self.beat_ets.last_at_realtime - prevlast_diff_secs

