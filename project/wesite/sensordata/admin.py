from django.contrib import admin
from .models import SensorRecord, VenueEvent, Alert

# Register your models here.
admin.site.register(SensorRecord)
admin.site.register(VenueEvent)  
admin.site.register(Alert)  