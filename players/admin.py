from django.contrib import admin
from .models import Die, Message, Roll, Room, Tally

# Register your models here.
admin.site.register(Die)
admin.site.register(Message)
admin.site.register(Roll)
admin.site.register(Room)
admin.site.register(Tally)

