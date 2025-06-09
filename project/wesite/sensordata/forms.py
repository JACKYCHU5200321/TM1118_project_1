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
        