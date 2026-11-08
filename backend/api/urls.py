from django.urls import path
from . import views
urlpatterns=[path('health/',views.health),path('classify/',views.classify),path('metrics/',views.metrics),path('models/',views.models),path('feedback/',views.feedback)]
