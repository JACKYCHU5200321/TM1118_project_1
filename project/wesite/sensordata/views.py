from django.shortcuts import render
from datetime import datetime, timedelta
import pytz
from . import sensor_mqtt
from .models import SensorRecord, VenueEvent, Alert
from .forms import QueryForm, NodeForm
from django.http import HttpResponseNotFound
from django.http import JsonResponse
from django.core import serializers
from django.db.models import Avg, Min, Max



latestsummary_stat = ['temp', 'hum', 'snd', 'light']
latestsummary_summ = [Avg, Min, Max]

def json_latestsummary(request):
    now = datetime.now()
    hourago = datetime.now() - timedelta(hours=1)
    records = SensorRecord.objects.filter(date_created__range=(hourago, now))
    locs = [x["loc"] for x in records.values("loc").distinct()]

    summary = dict()
    for l in locs:
        nodes = [x["node_id"] for x in records.filter(loc=l).values("node_id").distinct()]
        summary[l] = dict()
        for node in nodes:
            summary[l][node] = dict()
            for stat in latestsummary_stat:
                summary[l][node][stat] = dict()
                for summ in latestsummary_summ:
                    avg = records.filter(loc=l, node_id=node).aggregate(Avg(stat))
                    mn  = records.filter(loc=l, node_id=node).aggregate(Min(stat))
                    mx  = records.filter(loc=l, node_id=node).aggregate(Max(stat))
                    summary[l][node][stat]['avg'] = avg["%s__avg" % stat]
                    summary[l][node][stat]['min'] =  mn["%s__min" % stat]
                    summary[l][node][stat]['max'] =  mx["%s__max" % stat]

    return JsonResponse(summary, safe=False)

def json_records(request):
    now = datetime.now()
    dayago = datetime.now() - timedelta(hours=24)
    events = SensorRecord.objects.filter(date_created__range=(dayago, now))
    data = serializers.serialize('json', events) #Translating Django models into JSON formats
    return JsonResponse(data, safe=False)


datajsonPosval = ['temp', 'hum', 'snd', 'light']

def datajsonSerRes(ty):
    records_temp  = SensorRecord.objects.all()
    data = serializers.serialize('json', records_temp, fields=('date_created', 'loc', ty))
    return JsonResponse(data, safe=False)

def json_data(request, ty):
    if ty in datajsonPosval:
        return datajsonSerRes(ty)
    return page_not_found(request, "")

def page_not_found(request, any):
    # Custom 404 page context
    context = {
        'title': '404 - Page Not Found',
        'message': 'Sorry, we couldn’t find the page you were looking for. Please check the URL or return home.'
    }
    return render(request, 'sensordata/404page.html', context, status=404)

def home(request):
    return render(request, 'sensordata/homepage.html')

def member(request):
    return render(request, 'sensordata/memberlist.html')

class Linechart:
    def __init__(self, id, labels, values, value_name, title, node_id):
        self.id = id
        self.labels = labels
        self.values = values
        self.value_name = value_name
        self.title = title
        self.node_id = node_id

class ChartGroup:
    def __init__(self, name):
        self.name = name
        self.group = []
    def add(self, chart):
        self.group.append(chart)


def valuesMap2jsArray(values, f):
    return str([str(f(x)) for x in values]).replace("'", '"')


def page_listrecords(request):
    records = SensorRecord.objects.order_by("-date_created").all()
    context = {'records': records}
    return render(request, 'sensordata/recordlist.html', context)

alert_display_descript ={
    'robber': 'Unusual Sound Activity',
    'hot'   : 'Unusual High Temperature',
    'cold'  : 'Unusual Low Temperature'
}

def page_alert(request):
    records = Alert.objects.order_by("-time").all()
    
    for record in records:
        record.type_alert = alert_display_descript[record.type_alert]
    context = {'alerts': records}
    return render(request, 'sensordata/alert.html', context)

# statchart_title = ['temperature', 'Humidity', 'Sound level', 'Light Level']
# statchart_color = ['158, 240, 158', '54, 162, 235', '255, 206, 86', '75, 192, 192']

statchart_theme = {
    "temp" : ('Temperature', '158, 240, 158', "temperature(°C)", lambda x: x.temp),
    "hum"  : (   'Humidity',  '54, 162, 235', "humdity(%)",      lambda x: x.hum),
    "snd"  : ('Sound level',  '255, 206, 86', "sound level(dB)", lambda x: x.snd),
    "light": ('Light Level',  '75, 192, 192', "light level(%)",  lambda x: x.light),
}

def page_statchart(request, ty):
    if ty not in statchart_theme.keys():
        return

    loc = list({record.loc for record in SensorRecord.objects.all()})
    title, color, label, func = statchart_theme[ty]
    charts = []

    for l in loc:
        g_temp = ChartGroup(l)
        nodes = [x["node_id"] for x in SensorRecord.objects.filter(loc=l).values("node_id").distinct()]
        for node in nodes:
            records = SensorRecord.objects.filter(loc=l, node_id=node).all()
            records_temp  = valuesMap2jsArray(records, func)
            records_time = str([datetime.strftime(record.date_created, "%m/%d %H:%M") for record in records])
            g_temp.add(Linechart("%s_%s_temp"  % (node, l), records_time, records_temp,  label, "%s %s" % (l, title), node))
        charts.append(g_temp)
    context = {'chart_color': color, 'charts': charts}
    return render(request, 'sensordata/statchart.html', context)
    
def query_context_record(start, end, room):
    records = SensorRecord.objects.filter(loc=room).all()
    nodes = [x["node_id"] for x in records.values("node_id").distinct()]
    g_temp, g_hum, g_snd, g_light = ChartGroup("Temperature"), ChartGroup("Humidity"), ChartGroup("Sound Level"), ChartGroup("Light Level")
    for node in nodes:
        records = SensorRecord.objects.filter(loc=room, node_id=node).all()
        between_records = [record for record in records if
            record.date_created >= start and
            record.date_created <= end]
        records_temp  = valuesMap2jsArray(records, lambda x: x.temp)
        records_humi  = valuesMap2jsArray(records, lambda x: x.hum)
        records_snd   = valuesMap2jsArray(records, lambda x: x.snd)
        records_light = valuesMap2jsArray(records, lambda x: x.light)

        records_time = str([datetime.strftime(record.date_created, "%m/%d %H:%M") for record in between_records])

        g_temp.add(Linechart("%s_temp"  % node, records_time, records_temp,  "temperature(°C)", "%s Temperature" % room, node))
        g_hum.add(Linechart("%s_humi"  % node, records_time, records_humi,  "humdity(%)", "%s Humidity" % room, node))
        g_snd.add(Linechart("%s_snd"   % node, records_time, records_snd,   "sound level(dB)", "%s Sound Level" % room, node))
        g_light.add(Linechart("%s_light" % node, records_time, records_light, "light level(%)", "%s Light Level" % room, node))
    
    charts = [g_temp, g_hum, g_snd, g_light]
    return {'charts': charts}

def query_context_event(start, end, room):
    records = VenueEvent.objects.filter(loc=room, begin__range=(start, end), end__range=(start, end))
    nodes = SensorRecord.objects.filter(loc=room, date_created__range=(start, end))
    stats = nodes.aggregate(
        temp__avg=Avg('temp'), temp__min=Min('temp'), temp__max=Max('temp'),
        hum__avg=Avg('hum'), hum__min=Min('hum'), hum__max=Max('hum'),
        snd__avg=Avg('snd'), snd__min=Min('snd'), snd__max=Max('snd'),
        light__avg=Avg('light'), light__min=Min('light'), light__max=Max('light'),
    )
    events_table = str(["""{start: \"%s\", end: \"%s\", location: \"%s\", Event: \"%s\", instructor: \"%s\",\
                            temp : {avg: \"%s\", min: \"%s\", max: \"%s\" },\
                            hum  : {avg: \"%s\", min: \"%s\", max: \"%s\" },\
                            snd  : {avg: \"%s\", min: \"%s\", max: \"%s\" },\
                            light: {avg: \"%s\", min: \"%s\", max: \"%s\" }}""".replace('\n','') %
            (
                datetime.strftime(event.begin, "%Y-%m-%dT%H:%M:%S"),
                datetime.strftime(event.end, "%Y-%m-%dT%H:%M:%S"),
                event.loc, event.event, event.instructor,
                "%.2f" % stats["temp__avg"], stats["temp__min"], stats["temp__max"],
                "%.2f" % stats["hum__avg"],   stats["hum__min"],   stats["hum__max"],
                "%.2f" % stats["snd__avg"],   stats["snd__min"],   stats["snd__max"],
                "%.2f" % stats["light__avg"], stats["light__min"], stats["light__max"],
            ) for event in records]).replace("'", '')
    return {'events_table': events_table}



def context_recordNevent(start, end, room):
    uq_tstart, uq_tend = start, end

    records = SensorRecord.objects.filter(loc=room).all()
    events = VenueEvent.objects.filter(loc=room).all() 

    nodes = [x["node_id"] for x in records.values("node_id").distinct()]
    g_temp, g_hum, g_snd, g_light = ChartGroup("Temperature"), ChartGroup("Humidity"), ChartGroup("Sound Level"), ChartGroup("Light Level")
    
    
    for node in nodes:
        records = SensorRecord.objects.filter(loc=room, node_id=node).all()
        between_records = [record for record in records if
            record.date_created >= uq_tstart and
            record.date_created <= uq_tend]
        records_temp  = valuesMap2jsArray(records, lambda x: x.temp)
        records_humi  = valuesMap2jsArray(records, lambda x: x.hum)
        records_snd   = valuesMap2jsArray(records, lambda x: x.snd)
        records_light = valuesMap2jsArray(records, lambda x: x.light)

        records_time = str([datetime.strftime(record.date_created, "%m/%d %H:%M") for record in between_records])

        g_temp.add(Linechart("%s_temp"  % node, records_time, records_temp,  "temperature(°C)", "%s Temperature" % room, node))
        g_hum.add(Linechart("%s_humi"  % node, records_time, records_humi,  "humdity(%)", "%s Humidity" % room, node))
        g_snd.add(Linechart("%s_snd"   % node, records_time, records_snd,   "sound level(dB)", "%s Sound Level" % room, node))
        g_light.add(Linechart("%s_light" % node, records_time, records_light, "light level(%)", "%s Light Level" % room, node))
    
    charts = [g_temp, g_hum, g_snd, g_light]
    
    between_events = [event for event in events if
        event.begin >= uq_tstart and
        event.end <= uq_tend]

    events_table = str(["{start: \"%s\", end: \"%s\", location: \"%s\", Event: \"%s\", instructor: \"%s\"}" %
            (
                datetime.strftime(event.begin, "%Y-%m-%dT%H:%M:%S"),
                datetime.strftime(event.end, "%Y-%m-%dT%H:%M:%S"),
                event.loc, event.event, event.instructor
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
            context = query_context_record(start, end, room)
            return render(request, 'sensordata/timenode.html', context)
    else:
        form = QueryForm([(x, x) for x in loc])
    return render(request, 'sensordata/query.html', {'form': form})    

def page_queryevent(request):
    records = SensorRecord.objects.all()
    loc = list({record.loc for record in records})
    if request.method == 'POST':
        form = QueryForm([(x, x) for x in loc], request.POST)
        if form.is_valid():
            room = form.cleaned_data['room']
            start = form.cleaned_data['start']
            end = form.cleaned_data['end']
            context = query_context_event(start, end, room)
            return render(request, 'sensordata/timeevent.html', context)
    else:
        form = QueryForm([(x, x) for x in loc])
    return render(request, 'sensordata/query.html', {'form': form})

def page_node(request):
    records = SensorRecord.objects.all()
    nodes = list({record.node_id for record in records})
    if request.method == 'POST':
        form = NodeForm([(x, x) for x in nodes], request.POST)
        if form.is_valid():
            node = form.cleaned_data['node']
            g_temp, g_hum, g_snd, g_light = ChartGroup("Temperature"), ChartGroup("Humidity"), ChartGroup("Sound Level"), ChartGroup("Light Level")
            loc = [x["loc"] for x in SensorRecord.objects.filter(node_id=node).values("loc").distinct()]
            for room in loc:
                records = SensorRecord.objects.filter(loc=room, node_id=node).all()
                records_temp  = valuesMap2jsArray(records, lambda x: x.temp)
                records_humi  = valuesMap2jsArray(records, lambda x: x.hum)
                records_snd   = valuesMap2jsArray(records, lambda x: x.snd)
                records_light = valuesMap2jsArray(records, lambda x: x.light)

                records_time = str([datetime.strftime(record.date_created, "%m/%d %H:%M") for record in records])

                g_temp.add(Linechart("%s_%s_temp"  % (room, node), records_time, records_temp,  "temperature(°C)", "%s Temperature" % room, room))
                g_hum.add(Linechart("%s_%s_humi"  % (room, node), records_time, records_humi,  "humdity(%)", "%s Humidity" % room, room))
                g_snd.add(Linechart("%s_%s_snd"   % (room, node), records_time, records_snd,   "sound level(dB)", "%s Sound Level" % room, room))
                g_light.add(Linechart("%s_%s_light" % (room, node), records_time, records_light, "light level(%)", "%s Light Level" % room, room))
                
            charts = [g_temp, g_hum, g_snd, g_light]
            context = {'charts': charts}
            return render(request, 'sensordata/nodechart.html', context)
    else:
        form = NodeForm([(x, x) for x in nodes])
    return render(request, 'sensordata/node.html', {'form': form})    



# # Create your views here.
# def page_timeevent(request):
#     # uq_loc, uq_tstart, uq_tend = user_query()
#     uq_tstart, uq_tend = datetime.now() - timedelta(hours=1), datetime.now() + timedelta(hours=5)

#     records = SensorRecord.objects.all()
#     events = VenueEvent.objects.all()    

#     # all unique location
#     loc = list({record.loc for record in records})

#     # get in between records and events
#     between_records = [record for record in records if
#         record.date_created >= uq_tstart and
#         record.date_created <= uq_tend]
#     between_events = [event for event in events if
#         event.begin >= uq_tstart and
#         event.end <= uq_tend]

#     records_temp = str([str(record.temp) for record in between_records]).replace("'", '"')
#     records_time = str([datetime.strftime(record.date_created, "%H:%M") for record in between_records])

#     events_table = str(["{start: \"%s\", end: \"%s\", location: \"%s\", Event: \"%s\", instructor: \"%s\"}" %
#             (
#                 datetime.strftime(event.begin, "%Y-%m-%dT%H:%M:%S"),
#                 datetime.strftime(event.end, "%Y-%m-%dT%H:%M:%S"),
#                 event.loc, event.event, event.instructor
#             ) for event in between_events]).replace("'", '')
        
#     context = {'records_temp': records_temp, 'records_time': records_time, 'events_table': events_table}

    
#     return render(request, 'sensordata/timeevent.html', context)