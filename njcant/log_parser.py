import re

from device_baseclass import AntDataPoint
from hrm_device import HrmDataPoint
from sc_device import SpeedCadenceDataPoint

devtype2class = { 120: HrmDataPoint, 121: SpeedCadenceDataPoint }

def parse_loglines(line_source):
	""" Parse the lines output by the antlog script

		Given an iterable of lines as written by the antlog script, generate
		AntDataPoint objects representing the lines.

		Lines that don't look like ant data points are returned as strings.
	"""
	linere = re.compile(r'^([0-9.]+)\s+([0-9.fp]+)((?:\s+\d+){8})$')
	dev2prev = {}
	for line in line_source:
		hit = linere.match(line.strip())
		if hit:
			timestamp = float(hit.group(1))
			devspec = hit.group(2)
			devtype = int(devspec.split('.')[0])
			payload = [int(x) for x in hit.group(3).strip().split()]
			datapoint_class = devtype2class.get(devtype, 'AntDataPoint')
			prev_dp = dev2prev.get(devspec, None)
			dp = datapoint_class(timestamp=timestamp, devspec=devspec, payload=payload, prev_dp=prev_dp)
			dev2prev[devspec] = dp
			yield dp
		else:
			yield line.strip()
