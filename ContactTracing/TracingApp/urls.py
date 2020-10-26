from django.urls import path
from . import views
from django.conf.urls import url
from django import views as django_views
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
    path('add-contact/<str:cttype>/<int:pid>', views.add_contact, name='add-contact'),
    path('follow-up/<str:cttype>/<int:pid>', views.followup, name='follow-up'),
    path('assign', views.assign_contacts_cases, name='assign'),
    path('household/new', views.create_household, name='new-household'),
    path('link-cases/C/<int:case_id>', views.create_cluster_from, name='new-cluster-from'),
    path('investigate/C/<int:case_id>/cluster/<int:cluster_id>', views.edit_case_cluster, name='edit-case-cluster'),
    path('link-cases/new', views.create_cluster, name='new-cluster'),
    path('link-cases/edit/<int:cluster_id>', views.edit_cluster, name='edit-cluster'),
    path('search/', views.search_results, name='search_results'),
    url(r'^jsi18n/$', django_views.i18n.JavaScriptCatalog.as_view(), name='jsi18n'),
    url(r'^password/$', views.change_password, name='change_password'),
]
