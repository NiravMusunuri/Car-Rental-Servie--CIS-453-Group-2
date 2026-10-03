from decimal import Decimal
from django.core.management.base import BaseCommand
from rentals.models import Category, Car
class Command(BaseCommand):
    help = "Create sample fleet idempotently. Does not create accounts or overwrite existing cars."
    def handle(self, *args, **options):
        for name,rate,cars in [
            ("Economy","39.00",[("Toyota","Corolla",5,"Automatic","available"),("Honda","Fit",5,"Manual","available")]),
            ("SUV","69.00",[("Toyota","RAV4",5,"Automatic","available"),("Ford","Explorer",7,"Automatic","maintenance")]),
            ("Luxury","109.00",[("BMW","330i",5,"Automatic","available"),("Mercedes-Benz","C-Class",5,"Automatic","reserved")]),
        ]:
            category,_ = Category.objects.get_or_create(name=name,defaults={"daily_rate":Decimal(rate)})
            for make,model,seats,transmission,status in cars:
                Car.objects.get_or_create(make=make,model=model,year=2025,category=category,defaults={"seats":seats,"transmission":transmission,"status":status})
        self.stdout.write(self.style.SUCCESS("Sample fleet ready: 3 categories and 6 cars."))
