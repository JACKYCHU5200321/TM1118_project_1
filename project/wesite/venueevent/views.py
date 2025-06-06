from django.shortcuts import render
from . import sensor_mqtt
from .models import VenueEvent

# Create your views here.
def index(request):
    events = VenueEvent.objects.order_by('-date_created')
    context = {'events' : events}
    return render(request, 'venueevent/index.html', context)