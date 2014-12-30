# Some ANT+ devices include event data in the periodic data broadcast messages.
# These events are things like individual heart beats for a heart rate monitor,
# or the magnet passing the sensor for a cycling speed/cadence device.
# 
# The devices report the total number of occurrences of the event, and the time
# (in device clock ticks, usually 1024 ticks per second) at which the most recent
# event occurred.
#
# Code for dealing with this data at a device independent level goes here.

class AntEventTimerSpec(object):
	"Specifies the behaviour of an ant+ event timer"
	def __init__(self, event_desc, ticks_per_sec=1024.0, event_count_wrap=256, clock_wrap=256*256):
		self.event_desc = event_desc
		self.ticks_per_sec = ticks_per_sec
		self.event_count_wrap = event_count_wrap
		self.clock_wrap = clock_wrap

class AntEventTimerSample(object):
	""" A single ant+ event timer sample

		Encapsulates a single event timer value, consisting of an event
		count and the time of the most recent event.
	"""

	def __init__(self, spec, event_count, last_event_at, prev_sample):
		# Access to the previous sample (if any) from the same device
		# allows the constructor to correct for overflows of the 8-bit
		# or 16-bit event_count and last_event_at fields broadcast by
		# the device.
		self.raw_count = event_count
		self.raw_last_at = last_event_at

		if prev_sample is None:
			self._count_wraps = 0
			self._clock_wraps = 0
			self.count = event_count
			self.last_at_ticks = last_event_at
		else:
			self._count_wraps = prev_sample._count_wraps
			if self.raw_count < prev_sample.raw_count:
				self._count_wraps += 1
			self.count = event_count + spec.event_count_wrap * self._count_wraps

			self._clock_wraps = prev_sample._clock_wraps
			if self.raw_last_at < prev_sample.raw_last_at:
				self._clock_wraps += 1
			self.last_at_ticks = last_event_at + spec.clock_wrap * self._clock_wraps

		self.last_at_secs = float(self.last_at_ticks) / spec.ticks_per_sec
		self.last_at_realtime = None

	def __str__(self):
		last_at_str = '%d,%d' % (self._clock_wraps, self.raw_last_at)
		if self.last_at_realtime is not None:
			last_at_str += ',%f' % self.last_at_realtime
		return 'count=(%d,%d) last=(%s)' % (self._count_wraps, self.raw_count, last_at_str)

	def set_realtime(self, clock_offset):
		self.last_at_realtime = self.last_at_secs + clock_offset

	def get_clock_offset(self):
		if self.last_at_realtime is None:
			return None
		else:
			return self.last_at_realtime - self.last_at_secs


def add_realtimes_to_datapoint_list(data_points):
	""" Add event times in real time to timers within ANT samples

		Given a list of AntDataPoint objects received from a particular
		device, estimate the offset from real clock time for each independent
		clock in the device, and set the last_at_realtime field in the
		AntEventTimerSample object(s) embedded in each data point.
	"""
	if len(data_points) == 0:
		return
	timers_in_device = len(data_points[0].event_timers())

	for i in range(timers_in_device):
		estimate_clock_offset([(dp.timestamp, dp.event_timers()[i]) for dp in data_points], True)


def estimate_clock_offset(list_realtime_ets, set_last_at_realtime=True):
	""" Estimate event timer clock offset

		Given a list of (realtime, AntEventTimerSample), work out the offset
		between the ANT+ event timer clock and real clock time.

		Optionally update the last_at_realtime field in each of the sample
		objects to reflect the best available estimate of the real clock time
		at which the reported event occurred.
	"""
	prev_realtime = None
	prev_count = None
	weighted_sample_count = 0.0
	offset_total = 0.0
	for realtime, ets in list_realtime_ets:
		if prev_count is not None and ets.count > prev_count:
			realtime_diff = realtime - prev_realtime

			# If something went wrong causing received ANT+ broadcasts to be queued
			# before having the timestamps added, then several might seem to have
			# been sent at very nearly the same time.  Up to 4 per second is normal, so
			# less than 100ms between samples is suspicious.  If there is lag, the
			# timing data will be useless for working out the clock offset.
			if realtime_diff < 0.1:
				continue

			# The less the real time interval between samples, the more precisely the
			# real time at which the event occurred can be pinned down and so the higher
			# the sample should be weighted.
			sample_weight = 1.0 / realtime_diff

			count_diff = ets.count - prev_count
			mean_interevent_realtime = realtime_diff / count_diff
			last_event_probably_at = realtime - (mean_interevent_realtime / 2.0)
			sample_offset = last_event_probably_at - ets.last_at_secs
			offset_total += sample_weight * sample_offset
			weighted_sample_count += sample_weight
		prev_count = ets.count
		prev_realtime = realtime

	mean_offset = offset_total / weighted_sample_count

	if set_last_at_realtime:
		for _, ets in list_realtime_ets:
			ets.set_realtime(mean_offset)
			
	return mean_offset

