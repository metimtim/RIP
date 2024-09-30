from django.contrib import admin
from .models import Ship
from .models import Parking
from .models import ParkingShip

# Register your models here.
admin.site.register(Ship)
admin.site.register(Parking)


@admin.register(ParkingShip)
class ParkingShipAdmin(admin.ModelAdmin):
    list_display = ('parking_id', 'ship_id')
    search_fields = ('parking_id', 'ship_id')

# Register your models here.
