from django import forms

class QueryForm(forms.Form):
    start = forms.DateTimeField()
    end = forms.DateTimeField()
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