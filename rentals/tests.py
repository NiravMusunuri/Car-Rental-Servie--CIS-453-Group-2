from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from .models import Booking, Car, Category, Profile

User = get_user_model()

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class RentalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice', 'alice@example.com', 'StrongPass!274')
        self.other = User.objects.create_user('bob', 'bob@example.com', 'StrongPass!275')
        self.category = Category.objects.create(name='Economy', daily_rate=Decimal('39.00'))
        self.car = Car.objects.create(make='Toyota', model='Corolla', year=2025, category=self.category, seats=5, transmission='Automatic')
        self.start = timezone.localdate() + timedelta(days=5)
        self.end = self.start + timedelta(days=3)
    def booking(self, **kwargs):
        values = dict(car=self.car, customer=self.user, customer_name='Alice', customer_email=self.user.email, pickup_date=self.start, return_date=self.end)
        values.update(kwargs)
        return Booking.objects.create(**values)
    def sign_in(self):
        self.client.force_login(self.user)
    def dates(self, start=None, end=None):
        return {'pickup_date': str(start or self.start), 'return_date': str(end or self.end)}
    def test_registration_hashes_password_and_creates_profile(self):
        response = self.client.post(reverse('register'), dict(username='Charlie', email='CHARLIE@example.com', first_name='Charlie', last_name='Chen', password1='UniqueWord!284', password2='UniqueWord!284'))
        self.assertRedirects(response, reverse('car_list'))
        user = User.objects.get(username='charlie')
        self.assertTrue(user.check_password('UniqueWord!284'))
        self.assertEqual(user.email, 'charlie@example.com')
        self.assertTrue(Profile.objects.filter(user=user).exists())
    def test_duplicate_email_and_username_case_insensitive(self):
        data = dict(username='ALICE', email='ALICE@example.com', first_name='A', last_name='B', password1='UniqueWord!284', password2='UniqueWord!284')
        response = self.client.post(reverse('register'), data)
        self.assertContains(response, 'username already exists')
        self.assertContains(response, 'email already exists')
        self.assertEqual(User.objects.count(), 2)
    def test_password_mismatch(self):
        response = self.client.post(reverse('register'), dict(username='new', email='new@example.com', first_name='A', last_name='B', password1='UniqueWord!284', password2='different'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 2)
    def test_login_valid_invalid_and_post_logout(self):
        bad = self.client.post(reverse('login'), {'username':'alice','password':'bad'})
        self.assertContains(bad, 'Please enter a correct username and password')
        self.assertEqual(self.client.post(reverse('login'), {'username':'alice','password':'StrongPass!274'}).status_code, 302)
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        self.assertEqual(self.client.post(reverse('logout')).status_code, 302)
    def test_booking_requires_login(self):
        self.assertEqual(self.client.post(reverse('book_car', args=[self.car.pk]), self.dates()).status_code, 302)
        self.assertEqual(Booking.objects.count(), 0)
    def test_booking_total_and_owner_ignore_forged_price(self):
        self.sign_in()
        response = self.client.post(reverse('book_car', args=[self.car.pk]), {**self.dates(), 'total_price':'0', 'customer':self.other.pk})
        self.assertEqual(response.status_code, 302)
        item = Booking.objects.get()
        self.assertEqual(item.customer, self.user)
        self.assertEqual(item.total_price, Decimal('117.00'))
    def test_bad_dates(self):
        self.sign_in()
        for start,end in [(self.end,self.start),(self.start,self.start),(timezone.localdate()-timedelta(days=1),self.end)]:
            response = self.client.post(reverse('book_car', args=[self.car.pk]), self.dates(start,end))
            self.assertEqual(response.status_code, 200)
        self.assertEqual(Booking.objects.count(), 0)
    def test_conflict_and_adjacent_ranges(self):
        self.booking()
        for start,end in [(self.start,self.end),(self.start+timedelta(days=1),self.end+timedelta(days=1)),(self.start-timedelta(days=1),self.end+timedelta(days=1))]:
            with self.assertRaises(ValidationError):
                self.booking(pickup_date=start, return_date=end)
        self.booking(pickup_date=self.end, return_date=self.end+timedelta(days=1))
        self.assertEqual(Booking.objects.count(),2)
    def test_blocked_and_maintenance_not_bookable(self):
        for status in ['reserved','maintenance']:
            self.car.status=status
            self.car.save()
            with self.assertRaises(ValidationError):
                self.booking()
    def test_catalog_filters_and_invalid_input(self):
        self.booking()
        response=self.client.get(reverse('car_list'), {**self.dates(),'availability':'available'})
        self.assertNotContains(response,'Toyota Corolla')
        response=self.client.get(reverse('car_list'), {**self.dates(),'availability':'unavailable'})
        self.assertContains(response,'Toyota Corolla')
        self.assertContains(self.client.get(reverse('car_list'), {'category':'invalid'}), 'Select a valid choice')
        self.assertContains(self.client.get(reverse('car_list'), {'pickup_date':str(self.start)}), 'Enter both')
        self.assertContains(self.client.get(reverse('car_list'), {'transmission':'Manual'}), 'No matching cars')
    def test_booking_pages_private(self):
        item=self.booking()
        self.client.force_login(self.other)
        for name in ['booking_detail','modify']:
            self.assertEqual(self.client.get(reverse(name,args=[item.pk])).status_code,404)
        for name in ['pay','cancel']:
            self.assertEqual(self.client.post(reverse(name,args=[item.pk])).status_code,404)
        self.assertNotContains(self.client.get(reverse('my_bookings')),'Toyota Corolla')
    def test_mock_payment_decline_approve_and_repeat(self):
        item=self.booking()
        self.sign_in()
        url=reverse('pay',args=[item.pk])
        self.client.post(url, {'result':'declined','consent':'on'})
        item.refresh_from_db()
        self.assertEqual(item.payment_status,'unpaid')
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(url, {'result':'success','consent':'on'})
        item.refresh_from_db()
        self.assertEqual(item.payment_status,'paid')
        self.assertEqual(len(mail.outbox),1)
        self.client.post(url, {'result':'success','consent':'on'})
        self.assertEqual(len(mail.outbox),1)
    def test_payment_requires_consent(self):
        item=self.booking()
        self.sign_in()
        self.assertEqual(self.client.post(reverse('pay',args=[item.pk]),{'result':'success'}).status_code,200)
        item.refresh_from_db()
        self.assertEqual(item.payment_status,'unpaid')
    def test_cancel_refunds_and_releases_dates(self):
        item=self.booking(payment_status='paid')
        self.sign_in()
        self.client.post(reverse('cancel',args=[item.pk]))
        item.refresh_from_db()
        self.assertEqual((item.status,item.payment_status),('cancelled','refunded'))
        self.booking()
    def test_modify_retains_rate_and_rejects_conflict(self):
        item=self.booking(payment_status='paid')
        self.category.daily_rate=Decimal('99')
        self.category.save()
        self.sign_in()
        self.client.post(reverse('modify',args=[item.pk]),self.dates(end=self.end+timedelta(days=1)))
        item.refresh_from_db()
        self.assertEqual(item.total_price,Decimal('156'))
        self.assertEqual(item.payment_status,'unpaid')
        self.booking(pickup_date=self.end+timedelta(days=2),return_date=self.end+timedelta(days=4))
        response=self.client.post(reverse('modify',args=[item.pk]),self.dates(end=self.end+timedelta(days=3)))
        self.assertContains(response,'already booked')
        item.refresh_from_db()
        self.assertEqual(item.return_date,self.end+timedelta(days=1))
    def test_pickup_day_changes_rejected(self):
        item=self.booking(pickup_date=timezone.localdate())
        self.sign_in()
        self.client.post(reverse('cancel',args=[item.pk]))
        self.client.post(reverse('modify',args=[item.pk]),self.dates())
        item.refresh_from_db()
        self.assertEqual(item.status,'confirmed')
        self.assertEqual(item.pickup_date,timezone.localdate())
    def test_admin_access_and_model_validation(self):
        self.sign_in()
        self.assertEqual(self.client.get('/admin/rentals/car/').status_code,302)
        admin=User.objects.create_superuser('staff','staff@example.com','StrongPass!274')
        self.client.force_login(admin)
        for path in ['car','category','booking','profile']:
            self.assertEqual(self.client.get('/admin/rentals/'+path+'/').status_code,200)
        self.booking()
        from django.forms import modelform_factory
        Form=modelform_factory(Booking,fields=['car','customer_name','customer_email','pickup_date','return_date','status'])
        form=Form({'car':self.car.pk,'customer_name':'B','customer_email':'b@example.com',**self.dates(),'status':'confirmed'})
        self.assertFalse(form.is_valid())
        self.assertIn('already booked',str(form.errors))
    def test_profile_and_details_render(self):
        self.sign_in()
        self.client.post(reverse('profile'), {'phone':'555-0100','address':'123 Main St'})
        self.assertEqual(Profile.objects.get(user=self.user).phone,'555-0100')
        self.assertContains(self.client.get(reverse('car_detail',args=[self.car.pk])),'39.00')
    def test_csrf_protects_mutations(self):
        from django.test import Client
        client=Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        item=self.booking()
        self.assertEqual(client.post(reverse('cancel',args=[item.pk])).status_code,403)
        self.assertEqual(client.post(reverse('pay',args=[item.pk])).status_code,403)
    def test_seed_idempotent(self):
        call_command('seed_data',verbosity=0)
        count=Car.objects.count()
        call_command('seed_data',verbosity=0)
        self.assertEqual(Car.objects.count(),count)


class CarImageTests(TestCase):
    def test_admin_upload_render_clear_and_reject_invalid_image(self):
        import io
        import tempfile
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        category = Category.objects.create(name='Economy', daily_rate=39)
        car = Car.objects.create(make='Toyota', model='Corolla', year=2025, category=category, seats=5, transmission='Automatic')
        admin_user = User.objects.create_superuser('imageadmin', 'images@example.com', 'StrongPass!274')
        self.client.force_login(admin_user)
        url = reverse('admin:rentals_car_change', args=[car.pk])
        values = dict(make=car.make, model=car.model, year=2025, category=category.pk, seats=5, transmission='Automatic', status='available', _save='Save')
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            buffer = io.BytesIO()
            Image.new('RGB', (20, 10), 'white').save(buffer, format='PNG')
            response = self.client.post(url, {**values, 'image': SimpleUploadedFile('car.png', buffer.getvalue(), content_type='image/png')})
            self.assertEqual(response.status_code, 302)
            car.refresh_from_db()
            self.assertTrue(car.image.storage.exists(car.image.name))
            photo_response = self.client.get(car.image.url)
            self.assertEqual(photo_response.status_code, 200)
            self.assertEqual(photo_response["Content-Type"], "image/png")
            photo_response.close()
            self.assertEqual(self.client.get('/media/../db.sqlite3').status_code, 404)
            self.assertEqual(self.client.get('/media/cars/missing.png').status_code, 404)
            for route in [reverse('car_list'), reverse('car_detail', args=[car.pk])]:
                self.assertContains(self.client.get(route), car.image.url)
            self.assertContains(self.client.get(url), 'Current uploaded photo')
            response = self.client.post(url, {**values, 'image': SimpleUploadedFile('fake.png', b'not an image', content_type='image/png')})
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Upload a valid image')
            response = self.client.post(url, {**values, 'image-clear': 'on'})
            self.assertEqual(response.status_code, 302)
            car.refresh_from_db()
            self.assertFalse(car.image)
            self.assertContains(self.client.get(reverse('car_list')), 'toyota-corolla.png')
