
import datetime
import os

print("System time:", datetime.datetime.now())
print("UTC time:", datetime.datetime.utcnow())
print("TZ env var:", os.environ.get('TZ', 'Not set'))

