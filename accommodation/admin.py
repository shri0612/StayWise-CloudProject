

# Registering all the models used in the project.
from django.contrib import admin
from .models import Room, Booking,RoomImage
from .models import Profile

admin.site.register(Room)
admin.site.register(Booking)
admin.site.register(RoomImage)
admin.site.register(Profile)
