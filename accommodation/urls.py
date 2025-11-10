from django.urls import path
from . import views
from .api_auth_views import jwt_login

urlpatterns = [
    path('room_list/', views.room_list, name='room_list'),
    path('book/<str:room_id>/', views.book_room, name='book_room'),
    path('my_bookings/', views.my_bookings, name='my_bookings'),

  

    # Manager
    path('manager/dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/add-room/', views.add_room, name='add_room'),
    path('manager/edit-room/<str:room_id>/', views.edit_room, name='edit_room'),
    path('manager/delete-room/<str:room_id>/', views.delete_room, name='delete_room'),
    path('manager/delete-image/<str:image_id>/', views.delete_room_image, name='delete_room_image'),
    path('api/login/', jwt_login, name='jwt_login'),
]
