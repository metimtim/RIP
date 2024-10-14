from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from .serializers import *
from .models import Parking, Ship, ParkingShip
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import logout
from datetime import datetime


class ShipList(APIView):
    model_class = Ship
    serializer_class = ShipListSerializer


    # получить список кораблей
    def get(self, request):
        if 'class_name' in request.GET:
            ships = self.model_class.objects.filter(class_name__icontains=request.GET['class_name'], status='active')
        else:
            ships = self.model_class.objects.filter(status='active')

        serializer = self.serializer_class(ships, many=True)
        resp = serializer.data
        draft_request = Parking.objects.filter(user=request.user.id, status='draft').first()
        if draft_request:
            request_serializer = ParkingSerializer(draft_request)  # Use RequestSerializer here
            resp.append({'request': request_serializer.data})

        return Response(resp, status=status.HTTP_200_OK)


class ShipDetail(APIView):
    model_class = Ship
    serializer_class = ShipDetailSerializer

    # получить корабль
    def get(self, request, id_ship):
        ship = get_object_or_404(self.model_class, id_ship=id_ship)
        serializer = self.serializer_class(ship)
        return Response(serializer.data)

    # удалить корабль (для модератора)
    def delete(self, request, id_ship):

        # if not request.user.is_staff:
        #     return Response(status=status.HTTP_403_FORBIDDEN)

        ship = get_object_or_404(self.model_class, id_ship=id_ship)
        ship.status = 'deleted'
        ship.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # добавить новый корабль (для модератора)
    def post(self, request, format=None):
        # if not request.user.is_staff:
        #     return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # обновление корабля (для модератора)
    def put(self, request, id_ship, format=None):

        # if not request.user.is_staff:
        #     return Response(status=status.HTTP_403_FORBIDDEN)

        ship = get_object_or_404(self.model_class, id_ship=id_ship)
        serializer = self.serializer_class(ship, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddShipView(APIView):
    # добавление услуги в заявку
    def post(self, request):
        # создаем заявку, если ее еще нет
        if not Parking.objects.filter(user=request.user, status='draft').exists():
            new_parking = Parking()
            new_parking.user = request.user
            new_parking.save()


        id_parking = Parking.objects.filter(user=request.user, status='draft').first().id_parking
        serializer = ParkingShipSerializer(data=request.data)
        if serializer.is_valid():
            new_parking_ship = ParkingShip()
            new_parking_ship.ship_id = serializer.validated_data["id_ship"]
            new_parking_ship.parking_id = id_parking
            if 'captain' in request.data:
                new_parking_ship.captain = request.data["captain"]
            new_parking_ship.save()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ImageView(APIView):
    def post(self, request):
        # if not request.user.is_staff:
        #    return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = AddImageSerializer(data=request.data)
        if serializer.is_valid():
            ship = Ship.objects.get(id_ship=serializer.validated_data['id_ship'])
            ship.img_url = serializer.validated_data['img_url']
            ship.save()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


# USER VIEWS
class UserRegistrationView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Личный кабинет (обновление профиля)
class UserUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = UserUpdateSerializer(instance=request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Аутентификация пользователя
class UserLoginView(APIView):
    def post(self, request):
        serializer = AuthTokenSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Деавторизация пользователя
class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()  # Удаляем токен
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ListParking(APIView):
    def get(self, request):
        if 'formed_at' in request.GET and 'status' in request.GET:
            parkings = Parking.objects.filter(formed_at__gte=request.GET['formed_at'], status=request.GET['status']).exclude(
                formed_at=None)
        else:
            parkings = Parking.objects.all()

        parkings_serializer = ParkingSerializer(parkings, many=True)
        return Response(parkings_serializer.data, status=status.HTTP_200_OK)


class GetParking(APIView):
    def get(self, request, id_parking):
        parking = get_object_or_404(Parking, id_parking=id_parking)
        serializer = ParkingSerializer(parking)

        parking_ships = ParkingShip.objects.filter(parking_id=parking.id_parking)
        ships_ids = []
        for parking_ship in parking_ships:
            ships_ids.append(parking_ship.ship_id)

        ships_in_parking = []
        for id_ship in ships_ids:
            ships_in_parking.append(get_object_or_404(Ship, id_ship=id_ship))

        ships_serializer = ShipListSerializer(ships_in_parking, many=True)
        response = serializer.data
        response['ships'] = ships_serializer.data

        return Response(response, status=status.HTTP_200_OK)

    def put(self, request, id_parking):
        serializer = PutParkingSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            parking = get_object_or_404(Parking, id_parking=id_parking)
            for attr, value in serializer.validated_data.items():
                setattr(parking, attr, value)
            parking.save()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FormParking(APIView):
    def put(self, request, id_parking):
        parking = get_object_or_404(Parking, id_parking=id_parking)
        if not parking.status == 'draft':
            return Response(status=status.HTTP_400_BAD_REQUEST)
        # if not request.user == req.user:
        #    return Response(status=status.HTTP_403_FORBIDDEN)

        # if animal.created_at > datetime.now():
        #     return Response(status=status.HTTP_400_BAD_REQUEST)

        if not parking.ended_at == None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        parking.formed_at = datetime.now()
        parking.status = 'formed'
        parking.save()
        return Response(status=status.HTTP_200_OK)


class ModerateParking(APIView):
    def put(self, request, id_parking):

        # if not request.user.is_staff:
        #    return Response(status=status.HTTP_403_FORBIDDEN)

        parking = get_object_or_404(Parking, id_parking=id_parking)
        serializer = AcceptParkingSerializer(data=request.data)
        if not parking.status == 'formed':
            return Response({'error': 'Заявка не сформирована'}, status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
            if serializer.validated_data['accept'] == True and parking.status:
                parking.status = 'completed'
                parking.moderator = request.user


            else:
                parking.status = 'cancelled'
                parking.moderator = request.user
                parking.ended_at = datetime.now()
            parking.save()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id_parking):
        parking = get_object_or_404(Parking, id_parking=id_parking)

        # TODO auth
        # if not request.user.is_staff or not request.user == Request:
        #    return Response(status=status.HTTP_403_FORBIDDEN)

        parking.status = 'deleted'
        parking.ended_at = datetime.now()
        parking.save()
        return Response(status=status.HTTP_200_OK)


class EditShipParking(APIView):
    def delete(self, request, id_parking):
        if 'id_ship' in request.data:
            record_m_to_m = get_object_or_404(ParkingShip, parking_id=id_parking, ship_id=request.data['id_ship'])
            record_m_to_m.delete()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id_parking):
        # if not request.user.is_staff:
        #     return Response(status=status.HTTP_403_FORBIDDEN)
        if 'id_ship' in request.data and 'captain' in request.data:
            record_m_to_m = get_object_or_404(ParkingShip, parking_id=id_parking, ship_id=request.data['id_ship'])
            record_m_to_m.captain = request.data['captain']
            record_m_to_m.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)

