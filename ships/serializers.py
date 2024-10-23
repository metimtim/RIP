from .models import Ship, Parking, ParkingShip
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate


class AddImageSerializer(serializers.Serializer):
    id_ship = serializers.IntegerField(required=True)
    img_url = serializers.CharField(required=True)

    def validate(self, data):
        id_ship = data.get('id_ship')

        # Дополнительная логика валидации, например проверка на существование этих id в базе данных
        if not Ship.objects.filter(id_ship=id_ship).exists():
            raise serializers.ValidationError(f"id_ship is incorrect")

        return data


class ParkingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parking
        fields = ["id_parking", "date_of_parking", "status", "created_at", "formed_at", "ended_at", "user_name", "moderator", "port", "spendings_of_crew"]


class PutParkingSerializer(serializers.ModelSerializer):
    date_of_parking = serializers.DateField()
    port = serializers.CharField()
    class Meta:
        model = Parking
        fields = ["date_of_parking", "port", "status", "created_at", "formed_at", "ended_at", "user_name", "moderator", "spendings_of_crew"]


class ShipDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ship
        fields = ["id_ship", "ship_name", "class_name", "status", "description"]


class ShipListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ship
        fields = ["id_ship", "ship_name", "description", "status", "class_name", "img_url"]


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ship
        fields = ["id_ship", "img_url"]


class ParkingShipSerializer(serializers.Serializer):
    id_ship = serializers.IntegerField(required=True)
    captain = serializers.CharField(required=False)

    def validate(self, data):
        id_ship = data.get('id_ship')

        # Дополнительная логика валидации, например проверка на существование этих id в базе данных
        if not Ship.objects.filter(id_ship=id_ship).exists():
            raise serializers.ValidationError(f"id_ship is incorrect")

        return data


# AUTH SERIALIZERS

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')


class AuthTokenSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if user is None:
            raise serializers.ValidationError("Неверные учетные данные")
        return {'user': user}


class CheckUsernameSerializer(serializers.Serializer):
    username = serializers.CharField()

    def validate(self, data):
        if not User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("Пользователь не существует")

        return data


class AcceptParkingSerializer(serializers.Serializer):
    accept = serializers.BooleanField()

class ShipListInParkingSerializer(serializers.ModelSerializer):
    captain = serializers.CharField(required=False)
    class Meta:
        model = Ship
        fields = ["id_ship", "ship_name", "class_name", "status", "captain"]