from django.db import models
from datetime import datetime
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone


class Ship(models.Model):
    id_ship = models.AutoField(primary_key=True, null=False, unique=True)
    ship_name = models.CharField(max_length=60, null=False)
    class_name = models.CharField(max_length=60, null=False)
    description = models.TextField(max_length=600, null=False)
    status = models.CharField(max_length=30, null=False)
    img_url = models.CharField(max_length=255, null=False)



    class Meta:
        managed = True
        db_table = 'ship'

class Parking(models.Model):
    id_parking = models.AutoField(primary_key=True, null=False, unique=True)
    status = models.CharField(max_length=30, null=False, default='draft')
    created_at = models.DateTimeField(null=False, default=datetime.now())
    formed_at = models.DateTimeField(null=True)
    ended_at = models.DateTimeField(null=True)
    date_of_parking = models.DateField(null=True, default=(timezone.now().date() + timedelta(days=1)))
    port = models.CharField(max_length=30, null=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    moderator = models.ForeignKey(User, max_length=50,null=True, on_delete=models.SET_NULL, related_name='moderator_id')


    class Meta:
        managed = True
        db_table = 'parking'

class ParkingShip(models.Model):
    parking = models.ForeignKey(Parking, on_delete=models.CASCADE, related_name='parking_ship')
    ship = models.ForeignKey(Ship, on_delete=models.CASCADE)
    captain = models.CharField(max_length=50,null=True)

    class Meta:
        managed = True
        db_table = 'parking_ship'
        constraints = [
            models.UniqueConstraint(fields=['parking', 'ship'], name='unique_parking_ship')
        ]