from django.urls import path
from . import views
# from .views import NewCaseForm

urlpatterns = [
    path('', views.index, name='index'),
    path('assignments', views.assigns, name='assignments'),
    path('cases', views.cases, name='cases'),
    path('contacts', views.contacts, name='contacts'),
    path('info/<str:cttype>/<int:pid>', views.info, name='info'),
    path('new-case', views.new_case, name='new-case'),
    path('test', views.new_person, name='test'),
    path('investigate/<str:cttype>/<int:pid>', views.case_investigation, name='case-investigation'),
]
