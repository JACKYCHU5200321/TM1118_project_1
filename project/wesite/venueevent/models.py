from django.db import models

# Create your models here.
class VenueEvent(models.Model):
    loc = models.TextField()
    begin = models.TimeField()
    end = models.TimeField()
    title = models.TextField()
    description = models.TextField()

    def __str__(self):
        return 'data #{}'.format(self.id)