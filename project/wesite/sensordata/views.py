from django.shortcuts import render
from datetime import datetime, timedelta
import pytz
from . import sensor_mqtt
from .models import SensorRecord, VenueEvent
from .forms import QueryForm
from django.http import HttpResponseNotFound
from django.http import JsonResponse
from django.core import serializers

def recordasjson(request):
    events = SensorRecord.objects.all()
    data = serializers.serialize('json', events) #Translating Django models into JSON formats
    return JsonResponse(data, safe=False)

def datajson(request, ty):
    records = SensorRecord.objects.all()
    if ty == "temp":
        records_temp  = valuesMap2jsArray(records, lambda x: x.temp)
        data = serializers.serialize('json', records_temp)
        return JsonResponse(data, safe=False)
        
    pass


def page_not_found(request, any):
    # Custom 404 page context
    context = {
        'title': '404 - Page Not Found',
        'message': 'Sorry, we couldn’t find the page you were looking for. Please check the URL or return home.'
    }
    return render(request, 'sensordata/404page.html', context, status=404)

def home(request):
    return render(request, 'sensordata/homepage.html')

class Linechart:
    def __init__(self, id, labels, values, value_name, title):
        self.id = id
        self.labels = labels
        self.values = values
        self.value_name = value_name
        self.title = title


def valuesMap2jsArray(values, f):
    return str([str(f(x)) for x in values]).replace("'", '"')


def page_listrecords(request):
    records = SensorRecord.objects.order_by("-date_created").all()
    context = {'records': records}
    return render(request, 'sensordata/recordlist.html', context)

def page_temperature(request):
    records = SensorRecord.objects.all()
    loc = list({record.loc for record in records})
    charts = []
    for l in loc:
        sub_rec = SensorRecord.objects.filter(loc=l).all()
        records_temp  = valuesMap2jsArray(sub_rec, lambda x: x.temp)
        records_time = str([datetime.strftime(record.date_created, "%m/%d %H:%M") for record in sub_rec])
        charts.append(
            Linechart("temp%s" % l, records_time, records_temp, "temperature", l)
        )
        # print("%s: %d" % (l, len(a)))
    context = {'charts': charts}
    return render(request, 'sensordata/list_temp.html', context)
    


def context_recordNevent(start, end, room):
    uq_tstart, uq_tend = start, end

    records = SensorRecord.objects.filter(loc=room).all()
    events = VenueEvent.objects.filter(loc=room).all() 

    # all unique location
    # loc = list({record.loc for record in records})

    # get in between records and events
    between_records = [record for record in records if
        record.date_created >= uq_tstart and
        record.date_created <= uq_tend]
    between_events = [event for event in events if
        event.begin >= uq_tstart and
        event.end <= uq_tend]

    # records_temp = str([str(record.temp) for record in between_records]).replace("'", '"')
    # records_humi = str([str(record.hum) for record in between_records]).replace("'", '"')
    # records_snd = str([str(record.snd) for record in between_records]).replace("'", '"')
    # records_light = str([str(record.light) for record in between_records]).replace("'", '"')

    records_temp  = valuesMap2jsArray(records, lambda x: x.temp)
    records_humi  = valuesMap2jsArray(records, lambda x: x.hum)
    records_snd   = valuesMap2jsArray(records, lambda x: x.snd)
    records_light = valuesMap2jsArray(records, lambda x: x.light)

    records_time = str([datetime.strftime(record.date_created, "%m/%d %H:%M") for record in between_records])

    charts = [
        Linechart("temp", records_time, records_temp, "temperature", "room ___"),
        Linechart("humi", records_time, records_humi, "humdity", "room ___"),
        Linechart("snd", records_time, records_snd, "sound level", "room ___"),
        Linechart("light", records_time, records_light, "light level", "room ___")
    ]

    events_table = str(["{start: \"%s\", end: \"%s\", event: \"%s\", location: \"%s\", description: \"%s\"}" %
            (
                datetime.strftime(event.begin, "%Y-%m-%dT%H:%M:%S"),
                datetime.strftime(event.end, "%Y-%m-%dT%H:%M:%S"),
                event.title, event.loc, event.description
            ) for event in between_events]).replace("'", '')

    return {'events_table': events_table, 'charts': charts}


def page_query(request):
    records = SensorRecord.objects.all()
    loc = list({record.loc for record in records})
    if request.method == 'POST':
        form = QueryForm([(x, x) for x in loc], request.POST)

        if form.is_valid():
            room = form.cleaned_data['room']
            start = form.cleaned_data['start']
            end = form.cleaned_data['end']

            # records = SensorRecord.objects.filter(loc=room).values()
            # events = VenueEvent.objects.filter(loc=room).values()
            context = context_recordNevent(start, end, room)
            return render(request, 'sensordata/timeevent.html', context)
    else:
        
        form = QueryForm([(x, x) for x in loc])
        
        # print(dir(form))
        # form.fields['room'].choices = [(x, x) for x in loc]
        # form.fields['room'].widget.choices = [(x, x) for x in loc]
        # form.room.choices([(x, x) for x in loc])
    
    return render(request, 'sensordata/query.html', {'form': form})    



# Create your views here.
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

    records_temp = str([str(record.temp) for record in between_records]).replace("'", '"')
    records_time = str([datetime.strftime(record.date_created, "%H:%M") for record in between_records])

    events_table = str(["{start: \"%s\", end: \"%s\", event: \"%s\", location: \"%s\", description: \"%s\"}" %
            (
                datetime.strftime(event.begin, "%Y-%m-%dT%H:%M:%S"),
                datetime.strftime(event.end, "%Y-%m-%dT%H:%M:%S"),
                event.title, event.loc, event.description
            ) for event in between_events]).replace("'", '')
        
    context = {'records_temp': records_temp, 'records_time': records_time, 'events_table': events_table}

    
    return render(request, 'sensordata/timeevent.html', context)