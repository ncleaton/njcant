
# USB1 ANT stick interface. Running `dmesg | tail -n 25` after plugging the
# stick on a USB port should tell you the exact interface.

# SERIAL = '/dev/ttyUSB0'

# The ANT+ stick is my only USB serial thing, so scan for it.
import os
for x in range(10):
	SERIAL = '/dev/ttyUSB%d' % x
	if os.path.exists(SERIAL):
		break

# If set to True, the stick's driver will dump everything it reads/writes
# from/to the stick.
# Some demos depend on this setting being True, so unless you know what you
# are doing, leave it as is.
DEBUG = False

# Set to None to disable logging
LOG = None
#from ant.core import log
#LOG = log.LogWriter()

# From python-ant 
NETKEY = '\xB9\xA5\x21\xFB\xBD\x72\xC3\x45'

DEVSPECS = {
	'HRM': (120, 8070), # Heart rate monitor
	'SC':  (121, 8085), # Cycling speed/cadence sensor
}

