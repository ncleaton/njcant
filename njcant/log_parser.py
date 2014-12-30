import re

from njcant.hrm_device import HrmDataPoint

devname2class = { 'HRM': HrmDataPoint }

def parse_loglines(line_source):
	""" Parse the lines output by logger

		Given an iterable of lines as written by the logger script, generate
		HrmDataPoint objects representing the lines.

		Lines that can't be parsed into HrmDataPoint objects are returned as
		strings.
	"""
	linere = re.compile(r'^([0-9.]+)\s+(\w+)((?:\s+\d+){8})$')
	devname2prev = {}
	prev_timestamp = None
	for line in line_source:
		hit = linere.match(line.strip())
		if hit:
			timestamp = float(hit.group(1))
			devname = hit.group(2)
			payload = hit.group(3).strip()
			datapoint_class = devname2class.get(devname)
			if datapoint_class:
				prev_dp = devname2prev.get(devname)
				dp = datapoint_class(timestamp, [int(x) for x in payload.split()], prev_dp)
				devname2prev[devname] = dp
				prev_timestamp = dp.timestamp
				yield dp
			else:
				raise ValueError('unknown device name', (devname, line))
		else:
			yield line.strip()
				
				
