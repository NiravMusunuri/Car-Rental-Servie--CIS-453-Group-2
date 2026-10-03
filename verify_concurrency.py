import os
import sys
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from datetime import timedelta
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ['DJANGO_SETTINGS_MODULE'] = 'carrental.settings'
import django
from django.conf import settings
temp = tempfile.TemporaryDirectory()
settings.DATABASES['default']['NAME'] = str(Path(temp.name).resolve() / 'race.sqlite3')
django.setup()
from django.core.management import call_command
from django.db import connections
from django.core.exceptions import ValidationError
from django.utils import timezone
from rentals.models import Category, Car, Booking
call_command('migrate', verbosity=0)
category=Category.objects.create(name='Race',daily_rate='25.00')
car=Car.objects.create(make='Test',model='Race',year=2025,category=category,seats=5,transmission='Automatic')
barrier=Barrier(2)
def attempt(i):
    try:
        barrier.wait(timeout=10)
        Booking.objects.create(car_id=car.pk,customer_name=f'User {i}',customer_email=f'user{i}@example.com',pickup_date=timezone.localdate()+timedelta(days=2),return_date=timezone.localdate()+timedelta(days=4))
        return 'created'
    except ValidationError:
        return 'conflict rejected'
    finally:
        connections.close_all()
with ThreadPoolExecutor(max_workers=2) as pool:
    results=list(pool.map(attempt,range(2)))
assert sorted(results)==['conflict rejected','created'], results
assert Booking.objects.count()==1
print('PASS: simultaneous file-backed SQLite reservations: one created, one conflict rejected.')
connections.close_all()
temp.cleanup()

