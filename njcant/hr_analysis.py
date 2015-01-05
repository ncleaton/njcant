import math

from log_parser import parse_loglines
from event_timer import add_realtimes_to_datapoint_list

class HeartBeatTimings(object):
	def __init__(self, hrm_datapoint_iter):
		self.samples = list(_generate_beat_samples(hrm_datapoint_iter))

	def first_beat_time(self):
		return self.samples[0][0]

	def last_beat_time(self):
		return self.samples[-1][0]

	def __str__(self):
		duration = self.samples[-1][0] - self.samples[0][0]
		beats = self.samples[-1][1] - self.samples[0][1]
		samples = len(self.samples)
		return 'HeartBeatTimings: %d beats in %d samples over %f seconds from %f' % (beats, samples, duration, self.first_beat_time())

	def idx_last_datapoint_before(self, timestamp):
		if len(self.samples) == 0 or self.samples[0][0] >= timestamp:
			return None
		lower = 0
		upper = len(self.samples) - 1
		while upper > lower+1:
			mid = int((upper + lower) / 2)
			if self.samples[mid][0] >= timestamp:
				upper = mid
			else:
				lower = mid
		return lower

	def timeslice(self, from_time=None, to_time=None):
		"Return a subset of the data by time interval"
		return HeartBeatTimingsTimeslice(self, from_time, to_time)
		
	def realtimes_of_beats(self):
		""" Generate the real clock time of each heart beat

			Yield the time of each heartbeat the occured within the data set.
			Where there is incomplete data, use None as a placeholder for the
			beats whos exact time is unknown.
		"""
		prev_count = self.samples[0][1] - 1
		for timestamp, count in self.samples:
			beats_between_samples = count - prev_count
			if beats_between_samples > 1:
				for _ in xrange(beats_between_samples-1):
					yield None
			yield timestamp
			prev_count = count

	def compute_mean_hr_bpm(self):
		start_timestamp, start_count = self.samples[0]
		end_timestamp, end_count = self.samples[-1]

		exact_interval = end_timestamp - start_timestamp
		beats_over_interval = end_count - start_count
		hr_bps = beats_over_interval / exact_interval
		hr_bpm = 60 * hr_bps
		return hr_bpm

	def compute_hrv_ms(self):
		""" Compute a metric of heart rate variability

			http://en.wikipedia.org/wiki/Heart_rate_variability#Time-domain_methods

			This is an attempt at the "root mean square of successive differences"
			metric of HRV.  The result in is milliseconds.
		"""
		def hrv_sample(times):
			if None in times:
				return None
			int1 = times[1] - times[0]
			int2 = times[2] - times[1]
			int_diff = int2 - int1
			return int_diff * int_diff

		beattimes = list(self.realtimes_of_beats())
		if len(beattimes) < 3:
			return None
		total_var = 0
		sample_count = 0
		for i in xrange(len(beattimes)-2):
			var = hrv_sample(beattimes[i:i+3])
			if var is not None:
				total_var += var
				sample_count += 1
		if sample_count == 0:
			return None
		else:
			return 1000 * math.sqrt(total_var / sample_count)


class HeartBeatTimingsTimeslice(HeartBeatTimings):
	def __init__(self, parent, from_time, to_time):
		from_idx = None
		if from_time is not None:
			from_idx = parent.idx_last_datapoint_before(from_time)
		if from_idx is None:
			from_idx = 0

		to_idx = None
		if to_time is not None:
			to_idx = parent.idx_last_datapoint_before(to_time)
		if to_idx is None:
			to_idx = len(parent.samples) - 1

		self.samples = parent.samples[from_idx:to_idx+1]


def _generate_beat_samples(hrm_datapoint_iter):
	""" Generate the times of individual heart beats

		Yield a sequence of (last_beat_time, beat_count) tuples giving
		the clock time at which individual heart beats occurred and the
		cumulative beat count. Normally beat_count will increase by 1
		with each returned value, but it may jump by more if a gap
		in the data means that we have incomplete information.
	"""
	prev = None
	for dp in hrm_datapoint_iter:
		count = dp.beat_ets.count
		if prev is None:
			prev_beat_realtime = dp.prev_beat_realtime()
			if prev_beat_realtime is not None:
				yield prev_beat_realtime, count-1
			yield dp.beat_ets.last_at_realtime, count
		else:
			beats_in_interval = count - prev.beat_ets.count
			if beats_in_interval > 1:
				prev_beat_realtime = dp.prev_beat_realtime()
				if prev_beat_realtime is not None:
					yield prev_beat_realtime, count-1
			if beats_in_interval > 0:
				yield dp.beat_ets.last_at_realtime, count
		prev = dp
