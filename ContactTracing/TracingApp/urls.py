from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('assigns', views.assigns, name='assignments'),
    path('cases', views.cases, name='cases'),
    path('contacts', views.contacts, name='contacts'),
    path('info/<str:cttype>/<int:pid>', views.info, name='info')
]
