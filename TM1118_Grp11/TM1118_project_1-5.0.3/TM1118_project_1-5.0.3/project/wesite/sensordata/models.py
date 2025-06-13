from django.db import models

# Create your models here.
class SensorRecord(models.Model):
    node_id = models.TextField()
    loc = models.TextField()
    temp = models.DecimalField(max_digits=3, decimal_places=1)
    hum = models.DecimalField(max_digits=3, decimal_places=1)
    light = models.DecimalField(max_digits=5, decimal_places=1)
    snd = models.DecimalField(max_digits=5, decimal_places=1)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'SensorRecord #{}'.format(self.node_id)

class VenueEvent(models.Model):
    loc = models.TextField()
    begin = models.DateTimeField()
    end = models.DateTimeField()
    # title = models.TextField()
    # description = models.TextField()
    event = models.TextField()
    instructor = models.TextField()

    def __str__(self):
        return 'data #{}'.format(self.id)

class Alert(models.Model):
    node_id = models.TextField()
    loc = models.TextField()
    type_alert = models.TextField()
    time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'alert #{}'.format(self.id)