from django.shortcuts import render
from django.shortcuts import redirect
from django.db import connection
from .models import Ship, Parking, ParkingShip
from django.contrib.auth.models import User

def ships(request):
    if not Parking.objects.filter(status='draft').exists():
        ship_count = 0
        current_request = 0
    else:
        parkings = Parking.objects.filter(status='draft')
        current_request = parkings.first()
        ship_count = current_request.parking_ship.count()

    class_name = request.GET.get('class_name', '')
    if class_name:
        ships = Ship.objects.filter(class_name__icontains=class_name)
    else:
        ships = Ship.objects.all()

    return render(request, 'ships.html', {'data' : {
        'ships': ships,
        'count_ship': ship_count,
        'id_parking': current_request.id_parking if current_request else 0
    }})

def ship(request, id):
    current_ship = Ship.objects.get(id_ship=id)
    return render(request, 'ship.html', {'current_ship': current_ship})

def parking(request, id):
    if id == 0:
        return render(request, 'ship_request.html', {'current_request': None})

    if Parking.objects.filter(id_parking=id).exclude(status='draft').exists():
        return render(request, 'ship_request.html', {'current_request': None})

    if not Parking.objects.filter(id_parking=id).exists():
        return render(request, 'ship_request.html', {'current_request': None})

    req_id = id
    current_request = Parking.objects.get(id_parking=id)
    ship_ids = ParkingShip.objects.filter(parking=current_request).values_list('ship', flat=True)
    current_ships = Ship.objects.filter(id_ship__in=ship_ids)

    return render(request, 'ship_request.html', {'data' : {
        'current_ships': current_ships,
        'current_request': current_request,
        'req_id':req_id
    }})

def add_ship(request):
    if request.method == 'POST':
        if not Parking.objects.filter(status='draft').exists():
            parking = Parking()
            parking.user_id = request.user.id
            parking.save()
        else:
            parking = Parking.objects.get(status='draft')

        ship_id = request.POST.get('ship_id')
        new_ship = Ship.objects.get(id_ship=ship_id)
        if ParkingShip.objects.filter(parking=parking, ship=new_ship).exists():
            return redirect('/')
        parking_ship = ParkingShip(parking=parking, ship=new_ship)
        parking_ship.save()
        return redirect('/')
    else:
        return redirect('/')


def del_parking(request):
    if request.method == 'POST':
        id_parking = request.POST.get('id_parking')
        with connection.cursor() as cursor:
            cursor.execute("UPDATE parking SET status = %s WHERE id_parking = %s", ['deleted', id_parking])
        return redirect('/')
    else:
        return redirect('/')