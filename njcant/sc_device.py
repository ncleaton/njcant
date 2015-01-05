
from event_timer import AntEventTimerSpec, AntEventTimerSample
from device_baseclass import AntDataPoint

ets_specs = {
	'crank': AntEventTimerSpec(
		event_desc       = 'crank magnet at sensor',
		ticks_per_sec    = 1024.0,
		event_count_wrap = 256*256,
		clock_wrap       = 256*256,
	),
	'wheel': AntEventTimerSpec(
		event_desc       = 'wheel magnet at sensor',
		ticks_per_sec    = 1024.0,
		event_count_wrap = 256*256,
		clock_wrap       = 256*256,
	),
}

class SpeedCadenceDataPoint(AntDataPoint):
	def subclass_init(self, prev_dp):
		payload = self.raw_payload

		# The payload is 4 16-bit quantities: cumulative revolution count and
		# time of last magnet-at-sensor event, for both crank and wheel.
		self.raw_timecount = {
			'crank': (payload[0] + 256*payload[1], payload[2] + 256*payload[3]),
			'wheel': (payload[4] + 256*payload[5], payload[6] + 256*payload[7]),
		}

		for name, timecount in self.raw_timecount.items():
			time, count = timecount
			prev_ets = None if prev_dp is None else prev_dp.ets[name]
			self.ets[name] = AntEventTimerSample(ets_specs[name], count, time, prev_ets)

	def crank_ets(self):
		return self.ets['crank']
			
	def wheel_ets(self):
		return self.ets['wheel']

	def __str__(self):
		return "SC: " + AntDataPoint.__str__(self)
