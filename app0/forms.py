from django import forms

class frm(forms.Form):
    urls = forms.CharField(label='urls', max_length=1000)