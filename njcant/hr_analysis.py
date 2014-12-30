
from njcant.log_parser import parse_loglines
from njcant.event_timer import add_realtimes_to_datapoint_list


def compute_mean_hr_bpm(hrm_datapoint_iter):
	htc = heartbeat_time_count(hrm_datapoint_iter)
	start_timestamp, start_count = htc.next()
	for ts, count in htc:
		end_timestamp, end_count = ts, count
	
	exact_interval = end_timestamp - start_timestamp
	beats_over_interval = end_count - start_count
	hr_bps = beats_over_interval / exact_interval
	hr_bpm = 60 * hr_bps
	return hr_bpm


def heartbeat_time_count(hrm_datapoint_iter):
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
