from django.db import models
from django.db import models
from django.contrib.auth.models import User

class Room(models.Model):
    name = models.CharField(max_length=100)
    capacity = models.IntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    available = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Automatically set availability based on capacity
        self.available = self.capacity > 0
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
        


class Profile(models.Model):
    ROLE_CHOICES = [
        ('manager', 'Manager'),
        ('customer', 'Customer'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

        
class Booking(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    days = models.IntegerField()
    people = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=8, decimal_places=2)
    booked_on = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.name} - {self.room.name}"
        
        
class RoomImage(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='rooms/')

    def __str__(self):
        return f"Image for {self.room.name}"
