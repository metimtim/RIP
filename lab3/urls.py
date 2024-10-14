from django.contrib import admin
from ships import views
from django.urls import include, path
from rest_framework import routers

router = routers.DefaultRouter()

urlpatterns = [
    path('admin/', admin.site.urls),

    # Услуги
    path(r'ships/', views.ShipList.as_view(), name='ships-list'),  # список кораблей (GET),

    path(r'ships/<int:id_ship>/', views.ShipDetail.as_view(), name='ship-detail'),  # получить корабль (GET),
    path(r'ships/create/', views.ShipDetail.as_view(), name='ship-create'),  # добавление корабля (POST),
    path(r'ships/update/<int:id_ship>/', views.ShipDetail.as_view(), name='ship-update'), # обновление  корабля (PUT),
    path(r'ships/delete/<int:id_ship>/', views.ShipDetail.as_view(), name='ship-delete'), # удаление корабля (DELETE),

    path(r'ships/add/', views.AddShipView.as_view(), name='add-ship-to-parking'), # добавление Корабля в заявку (POST),

    path(r'ships/image/', views.ImageView.as_view(), name='add-image'),  # замена изображения

    # Заявки
    path(r'list-parkings/', views.ListParking.as_view(), name='list-parkings-by-username'), # получить заявки (GET),
    path(r'parking/<int:id_parking>/', views.GetParking.as_view(), name='get-parking-by-id'), # получить конкретную заявку (GET),
    path(r'parking/<int:id_parking>/', views.GetParking.as_view(), name='put-parking-by-id'), # изменить конкретную заявку (PUT),

    path(r'form-parking/<int:id_parking>/', views.FormParking.as_view(), name='form-parking-by-id'), #формирование заявки (PUT)
    path(r'moderate-parking/<int:id_parking>/', views.ModerateParking.as_view(), name='moderate-parking-by-id'), #завершить/отклонить модератором (PUT)
    path(r'delete-parking/<int:id_parking>/', views.ModerateParking.as_view(), name='delete-parking-by-id'), #удалить заявку (DELETE)

    # m-m
    path(r'delete-from-parking/<int:id_parking>/', views.EditShipParking.as_view(), name='delete-from-parking-by-id'), #удалить из заявки (DELETE)
    path(r'add-captain/<int:id_parking>/', views.EditShipParking.as_view(), name='add-captain-request-by-id'),

    # Users
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('profile/', views.UserUpdateView.as_view(), name='profile'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
]

