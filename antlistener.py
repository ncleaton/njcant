"""

Based on https://github.com/mvillalba/python-ant/blob/develop/demos/ant.core/07-rawmessage3.py
"""

import re, sys, time, datetime, Queue
from ant.core import driver
from ant.core import event
from ant.core.constants import *
from ant.core.message import *

class AntStick(object):
	""" Encapsulates an ANT+ USB stick

		A high level interface to an ANT+ USB stick, using the python-ant
		library for lower level operations.
	"""
	def __init__(self, serial_device):
		NETKEY = '\xB9\xA5\x21\xFB\xBD\x72\xC3\x45'

		msgq = Queue.Queue()
		class MyCallback(event.EventCallback):
			def process(self, msg):
				msgq.put((time.time(), msg))

		self.serial_device = serial_device
		self.msgq = msgq
		self.open_channels = []

		# Initialize driver
		self.stick = driver.USB1Driver(serial_device, log=None)
		self.stick.open()
 
		# Initialize event machine
		self.evm = event.EventMachine(self.stick)
		self.evm.registerCallback(MyCallback())
		self.evm.start()

		# Reset
		self.send_msg(SystemResetMessage(), expect_ack=False)
		time.sleep(1)

		# Set network key
		self.send_msg(NetworkKeyMessage(key=NETKEY))

	def send_msg(self, msg, expect_ack=True):
		self.stick.write(msg.encode())
		if expect_ack and self.evm.waitForAck(msg) != RESPONSE_NO_ERROR:
			raise StandardError('Stick did not accept command', msg)

	def receive_messages(self):
		while True:
			yield self.msgq.get()

	def open_channel(self, device_spec):
		""" Open a channel and start listening for messages on it

device_spec is a string specifying which ANT device(s) are acceptable.
The stick will pair this channel with the first matching device to come
within range.

The device_spec format is:

	TYPE[.UID][pPERIOD][fFREQUENCY]

* TYPE is the numeric ANT+ device type, for example 120 for heart rate
monitor. You can use 0 as a wildcard to listen for devices of any type.

* UID is the ANT+ unique ID of the device to which to listen, sometimes
referred to as the device number. The default is 0, which is a wildcard
matching any device of the correct type.

* PERIOD is the ANT+ period specification: 32768 divided by the
broadcast period in messages per second.  It should match the period at
which the device is broadcasting.  In my limited experience of playing
with ANT+ sensors, most devices broadcast around 4 messages per second,
with the exact period being slightly different for each device type. You
need to match the period of the device to which you are listening fairly
closely in order to capture everything that it broadcasts.  The default
is my best guess at what will work.

* FREQUENCY specifies the RF frequency on which the device is expected
to be transmitting. The default is 57, there's usually no need to change
it.
"""
		devtype, devuid, period, frequency = self._parse_dev_spec(device_spec)
		cnum = len(self.open_channels)
		self.send_msg(ChannelAssignMessage(number=cnum))
		self.send_msg(ChannelIDMessage(number=cnum, device_type=devtype, device_number=devuid))
		self.send_msg(ChannelSearchTimeoutMessage(number=cnum, timeout=255))
		self.send_msg(ChannelPeriodMessage(number=cnum, period=period))
		self.send_msg(ChannelFrequencyMessage(number=cnum, frequency=frequency))
		self.send_msg(ChannelOpenMessage(number=cnum))
		self.open_channels.append(device_spec)
		return cnum

	def _parse_dev_spec(self, devspec):
		hit = re.match(r'^(?P<type>\d+)(?:[.](?P<uid>\d+))?(?:p(?P<period>\d+))?(?:f(?P<freq>\d+))?$', devspec)
		if not hit:
			raise ValueError('malformed ANT+ device spec', devspec)
		devtype = int(hit.group('type'))
		uid = hit.group('uid')
		uid = 0 if uid is None else int(uid)
		period = hit.group('period')
		period = self._default_period(devtype) if period is None else int(period)
		freq = hit.group('freq')
		freq = 57 if freq is None else int(freq)
		return devtype, uid, period, freq

	def _default_period(self, devtype):
		return {
			120: 8070, # Heart rate monitor
			121: 8085, # Cycling speed/cadence sensor
		}.get(devtype, 8070)
