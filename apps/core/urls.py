from django.urls import path

from .views import HomePageView, start
urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('start/', start, name='start')
]
