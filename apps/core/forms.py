from django import forms


class ParseForm(forms.Form):
    email = forms.CharField(label='fb user email', max_length=100)
    password = forms.CharField(widget=forms.PasswordInput())
    url = forms.URLField(label='fb group url', required=False)
