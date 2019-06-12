
import sys

CACHE_LIFETIME = 10 * 60
if "debug" in sys.argv:
	CACHE_LIFETIME = 1
