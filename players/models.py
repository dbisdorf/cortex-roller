from django.db import models
from django.utils import timezone
import random
import uuid

class Room(models.Model):
    name = models.CharField(primary_key=True, max_length=30)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return '[{0}] {1}'.format(self.name, self.timestamp)

class Die(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    faces = models.IntegerField(default=4)
    result = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(default=timezone.now)
    tag = models.CharField(max_length=1, default='X')
    owner = models.UUIDField()

    def __str__(self):
        if self.result:
            return '[{0}] D{1}={2}'.format(self.room, self.faces, self.result)
        return '[{0}] D{1}=X'.format(self.room, self.faces)

    def roll(self):
        self.result = random.SystemRandom().randint(1, self.faces)


class Message(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(default=timezone.now)
    owner = models.UUIDField()

    def __str__(self):
        return '[{0}] {1}'.format(self.room, self.text)

class Roll(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(default=timezone.now)
    owner = models.UUIDField()

    def __str__(self):
        return '[{0}] {1}'.format(self.room, self.text)



