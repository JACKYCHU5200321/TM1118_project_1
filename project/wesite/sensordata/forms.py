from django import forms
from django.forms.widgets import SplitDateTimeWidget, TextInput

class QueryForm(forms.Form):
    start = forms.DateTimeField(widget=TextInput(
            attrs={'type': 'datetime-local', 'class': 'form-control'}
        ))
    end = forms.DateTimeField(widget=TextInput(
            attrs={'type': 'datetime-local', 'class': 'form-control'}
        ))
    room = forms.ChoiceField(
        label='Your choice',
        choices=[]
    )

    def __init__(self, rooms, *args, **kwargs):
      super(QueryForm, self).__init__(*args, **kwargs)
      
      self.fields['room'] = forms.ChoiceField(choices=rooms)

class NodeForm(forms.Form):
    node = forms.ChoiceField(
        label='Nodes',
        choices=[]
    )

    def __init__(self, nodes, *args, **kwargs):
      super(NodeForm, self).__init__(*args, **kwargs)
      
      self.fields['node'] = forms.ChoiceField(choices=nodes)