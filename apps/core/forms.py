from django import forms


class ParseForm(forms.Form):
    username = forms.CharField(label='fb username', max_length=100)
    password = forms.CharField(widget=forms.PasswordInput())
    url = forms.URLField(label='fb group', required=False)
