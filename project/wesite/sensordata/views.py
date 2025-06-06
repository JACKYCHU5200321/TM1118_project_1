from django.shortcuts import render
from datetime import datetime, timedelta
import pytz
from . import sensor_mqtt
from .models import SensorRecord
from .models import VenueEvent


# Create your views here.
def index(request):
    events = SensorRecord.objects.order_by('-date_created')
    context = {'events' : events}
    return render(request, 'sensordata/index.html', context)

def index2(request):
    events = VenueEvent.objects.order_by('-date_created')
    context = {'events' : events}
    return render(request, 'sensordata/index2.html', context)



def page_timeevent(request):
    # uq_loc, uq_tstart, uq_tend = user_query()
    uq_tstart, uq_tend = datetime.now() - timedelta(hours=1), datetime.now() + timedelta(hours=5)

    records = SensorRecord.objects.all()
    events = VenueEvent.objects.all()    

    # all unique location
    loc = list({record.loc for record in records})

    # get in between records and events
    between_records = [record for record in records if
        record.date_created >= uq_tstart and
        record.date_created <= uq_tend]
    between_events = [event for event in events if
        event.begin >= uq_tstart and
        event.end <= uq_tend]

    print("records:", between_records)
    print("events:", between_events)

    records_temp = str([str(record.temp) for record in between_records]).replace("'", '"')
    records_time = str([datetime.strftime(record.date_created, "%H:%M") for record in between_records])

    events_table = str(["{start: \"%s\", end: \"%s\", event: \"%s\", location: \"%s\", description: \"%s\"}" %
            (
                datetime.strftime(event.begin, "%Y-%m-%dT%H:%M:%S"),
                datetime.strftime(event.end, "%Y-%m-%dT%H:%M:%S"),
                event.title, event.loc, event.description
            ) for event in between_events]).replace("'", '')
    print(records_temp)
    print(records_time)
    context = {'records_temp': records_temp, 'records_time': records_time, 'events_table': events_table}

    
    return render(request, 'sensordata/a.html', context)