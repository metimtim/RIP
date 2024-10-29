from datetime import datetime
from random import randint

from django.contrib.auth import logout, login
from django.db.models import F
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import *

class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


class ShipList(APIView):
    model_class = Ship
    serializer_class = ShipListSerializer

    @swagger_auto_schema(
        operation_description="Получение списка кораблей. Можно отфильтровать по его классу.",
        manual_parameters=[
            openapi.Parameter('ship_name', openapi.IN_QUERY, description="Название класса корабля",
                              type=openapi.TYPE_STRING, default=""),
        ],
        responses={200: ShipListSerializer(many=True)}
    )
    # получить список кораблей
    def get(self, request):
        if 'class_name' in request.GET:
            ships = self.model_class.objects.filter(class_name__icontains=request.GET['class_name'])
        else:
            ships = self.model_class.objects.all()

        serializer = self.serializer_class(ships, many=True)
        resp = serializer.data
        draft_request = Parking.objects.filter(user=request.user, status='draft').first()

        if draft_request:
            draft_request_id = Parking.objects.filter(user=request.user, status='draft').first().id_parking
            count_ships_in_draft = ParkingShip.objects.filter(parking_id=draft_request).values_list('ship_id',
                                                                                                    flat=True).count()
            resp.append({'parking_id': draft_request_id})
            resp.append({'count': count_ships_in_draft})

        return Response(resp, status=status.HTTP_200_OK)


class ShipDetail(APIView):
    model_class = Ship
    serializer_class = ShipDetailSerializer

    @swagger_auto_schema(
        operation_description="Получить информацию о конкретном корабле.",
        responses={200: ShipDetailSerializer()}
    )
    # получить корабль
    def get(self, request, id_ship):
        ship = get_object_or_404(self.model_class, id_ship=id_ship)
        serializer = self.serializer_class(ship)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Удаление корабля по ID (moderators only).",
        responses={204: 'No Content', 403: 'Forbidden'}
    )
    # удалить корабль (для модератора)
    def delete(self, request, id_ship):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)

        ship = get_object_or_404(self.model_class, id_ship=id_ship)
        ship.status = 'deleted'
        ship.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_description="Добавление нового корабля (moderators only).",
        request_body=ShipDetailSerializer,
        responses={201: ShipDetailSerializer(), 400: 'Bad Request'}
    )
    # добавить новый корабль (для модератора)
    def post(self, request, format=None):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Обновление данных корабля (moderators only).",
        request_body=ShipDetailSerializer,
        responses={200: ShipDetailSerializer(), 400: 'Bad Request'}
    )
    # обновление корабля (для модератора)
    def put(self, request, id_ship, format=None):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)

        ship = get_object_or_404(self.model_class, id_ship=id_ship)
        serializer = self.serializer_class(ship, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddShipView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]
    # добавление услуги в заявку
    @swagger_auto_schema(
        operation_description="Добавление корабля в заявку-черновик пользователя. Создается новая заявка, если не существует заявки-черновика",
        responses={200: "корабль успешно добавлен в заявку", 404: "корабль не найден"},
        manual_parameters=[
            openapi.Parameter('id_ship', openapi.IN_PATH, description="Номер корабля", type=openapi.TYPE_INTEGER,
                              required=True)
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'captain': openapi.Schema(type=openapi.TYPE_NUMBER, description='Капитан корабля',
                                          example=10000)},
            required=[]
        )
    )
    def post(self, request):
        # создаем заявку, если ее еще нет
        if not Parking.objects.filter(user=request.user, status='draft').exists():
            new_parking = Parking()
            new_parking.user = request.user
            new_parking.user_name = request.user.username
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
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Upload an image for a ship.",
        request_body=AddImageSerializer,
        responses={201: "Image uploaded successfully", 400: "Bad request"}
    )
    def post(self, request):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)

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
    @swagger_auto_schema(
        operation_description="Регистрация нового пользователя.",
        request_body=UserRegistrationSerializer,
        responses={201: "User registered successfully", 400: "Bad request"}
    )
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Личный кабинет (обновление профиля)
class UserUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Обновление профиля аунтифицированного пользователя",
        request_body=UserUpdateSerializer,
        responses={200: UserUpdateSerializer(), 400: "Bad request"}
    )
    def put(self, request):
        serializer = UserUpdateSerializer(instance=request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Аутентификация пользователя
class UserLoginView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]

    @swagger_auto_schema(
        operation_description="Аутентификация пользователя с логином и паролем. Возвращает файл cookie сеанса в случае успеха.",
        request_body=AuthTokenSerializer,
        responses={200: "Login successful", 400: "Invalid credentials"}
    )
    def post(self, request):
        serializer = AuthTokenSerializer(data=request.data)
        if serializer.is_valid():
            username = request.data['username']
            password = request.data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)  # Сохраняем информацию о пользователе в сессии
                # random_key = uuid.uuid4()
                # session_storage.set(random_key, username)
                return Response({'message': 'Login successful'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Деавторизация пользователя
class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Выход аунтифицированного пользователя. Удаление сессии.",
        responses={204: "Logout successful"}
    )
    def post(self, request):
        logout(request)  # Удаляем сессию
        return Response({'message': 'Logout successful'}, status=status.HTTP_204_NO_CONTENT)


class ListParking(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Get a list of requests. Optionally filter by date and status.",
        manual_parameters=[
            openapi.Parameter('date', openapi.IN_QUERY, description="Filter requests after a specific date",
                              type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter('status', openapi.IN_QUERY, description="Filter requests by status",
                              type=openapi.TYPE_STRING)
        ],
        responses={200: ParkingSerializer(many=True)}
    )
    def get(self, request):
        if request.user.is_authenticated:
            if request.user.is_staff:
                if 'date' in request.data and 'status' in request.data:
                    parkings = Parking.objects.filter(formed_at__gte=request.data['date'],
                                                    status=request.data['status']).exclude(
                        formed_at=None)
                else:
                    parkings = Parking.objects.all().exclude(
                        formed_at=None)
            else:

                if 'date' in request.data and 'status' in request.data:
                    parkings = Parking.objects.filter(user=request.user, formed_at__gte=request.data['date'],
                                                      status=request.data['status']).exclude(
                        formed_at=None)
                else:
                    parkings = Parking.objects.filter(user=request.user).exclude(formed_at=None)

            parkings_serializer = ParkingSerializer(parkings, many=True)

            return Response(parkings_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Вы не вошли в аккаунт'}, status=status.HTTP_403_FORBIDDEN)

class GetParking(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Get details of a request by ID, including associated threats.",
        responses={200: ParkingSerializer()}
    )
    def get(self, request, id_parking):
        parking = get_object_or_404(Parking, id_parking=id_parking)
        serializer = ParkingSerializer(parking)
        response = serializer.data

        # parking_ships = ParkingShip.objects.filter(parking_id=parking.id_parking)
        # ships_ids = []
        # for parking_ship in parking_ships:
        #     ships_ids.append(parking_ship.ship_id)
        #
        # ships_in_parking = []
        # for id_ship in ships_ids:
        #     ships_in_parking.append(get_object_or_404(Ship, id_ship=id_ship))
        current_ships = Ship.objects.filter(
            ship_ship__parking_id=id_parking  # Проверка на соответствие стоянки
        ).annotate(
            captain=F('ship_ship__captain')  # Добавляем информацию о капитане из модели ParkingShip
        ).order_by('id_ship')
        ships_serializer = ShipListInParkingSerializer(current_ships, many=True)

        response['ships'] = ships_serializer.data

        return Response(response, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Update a request by ID.",
        request_body=PutParkingSerializer,
        responses={200: "Request updated successfully", 400: "Bad request"}
    )

    def put(self, request, id_parking):
        if request.user.is_authenticated:
            serializer = PutParkingSerializer(data=request.data, partial=True)
            if serializer.is_valid():
                parking = get_object_or_404(Parking, id_parking=id_parking)
                for attr, value in serializer.validated_data.items():
                    setattr(parking, attr, value)
                parking.save()
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'message': 'Вы не вошли в аккаунт'}, status=status.HTTP_403_FORBIDDEN)


class FormParking(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Mark a request as formed. Only available for requests with a 'draft' status.",
        responses={200: "Request successfully formed", 400: "Bad request"}
    )
    def put(self, request, id_parking):
        parking = get_object_or_404(Parking, id_parking=id_parking)
        if not parking.status == 'draft':
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if not request.user == parking.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        # if animal.created_at > datetime.now():
        #     return Response(status=status.HTTP_400_BAD_REQUEST)

        if not parking.ended_at == None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        parking.formed_at = datetime.now()
        parking.status = 'formed'
        parking.save()
        return Response(status=status.HTTP_200_OK)


class ModerateParking(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Approve or decline a request (for moderators).",
        request_body=AcceptParkingSerializer,
        responses={200: "Request moderated successfully", 400: "Bad request"}
    )
    def put(self, request, id_parking):

        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)

        parking = get_object_or_404(Parking, id_parking=id_parking)
        serializer = AcceptParkingSerializer(data=request.data)
        if not parking.status == 'formed':
            return Response({'error': 'Заявка не сформирована'}, status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
            if serializer.validated_data['accept'] == True and parking.status:
                parking.status = 'completed'
                parking.moderator = request.user
                count_ships_in_draft = ParkingShip.objects.filter(parking_id=id_parking).values_list('ship_id',
                                                                                                     flat=True).count()
                parking.spendings_of_crew = count_ships_in_draft * randint(10000, 20000)
                parking.ended_at = datetime.now()


            else:
                parking.status = 'cancelled'
                parking.moderator = request.user
                parking.ended_at = datetime.now()
            parking.save()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete a request (for moderators).",
        responses={200: "Request deleted successfully"}
    )
    def delete(self, request, id_parking):

        parking = get_object_or_404(Parking, id_parking=id_parking)

        parking.status = 'deleted'
        parking.ended_at = datetime.now()
        parking.save()
        return Response(status=status.HTTP_200_OK)


class EditShipParking(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Remove a threat from a request.",
        # request_body=openapi.Schema(
        #     type=openapi.TYPE_OBJECT,
        #     properties={'threat_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the threat")},
        #     required=['threat_id']
        # ),
        responses={200: "Threat removed successfully", 400: "Bad request"}
    )
    def delete(self, request, id_parking, id_ship):
        record_m_to_m = get_object_or_404(ParkingShip, parking_id=id_parking, ship_id=id_ship)
        record_m_to_m.delete()
        return Response(status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Update the captain of a ship in a request.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'captain': openapi.Schema(type=openapi.TYPE_NUMBER, description="Капитан корабля")
            },
            required=['captain']
        ),
        responses={200: "Captain updated successfully", 400: "Bad request"}
    )
    def put(self, request, id_parking, id_ship):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if 'captain' in request.data:
            record_m_to_m = get_object_or_404(ParkingShip, parking_id=id_parking, ship_id=id_ship)
            record_m_to_m.captain = request.data['captain']
            record_m_to_m.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


