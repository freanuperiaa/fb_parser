from django.urls import path

from . import views

urlpatterns = [
    path('start/', views.ParseView.as_view(), name='start')
]
