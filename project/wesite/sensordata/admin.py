from django.contrib import admin
from .models import SensorRecord
from .models import VenueEvent
# Register your models here.
admin.site.register(SensorRecord)
admin.site.register(VenueEvent)  