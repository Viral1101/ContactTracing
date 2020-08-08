from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound, Http404
from .models import *
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta

# Create your views here.


@login_required(login_url='/accounts/login/')
def index(request):
    return HttpResponse("This is the index.")


@login_required(login_url='/accounts/login/')
def assigns(request):
    types = AssignmentType.objects.all()
    current_user = request.user.id
    assignments = Assignments.objects.filter(user__id=current_user).order_by('assign_type')
    as_cases = assignments.filter(case__case_id__gte=0)
    as_contacts = assignments.filter(contact__contact_id__gte=0)
    outbreaks = assignments.filter(outbreak__outbreak_id__gte=0)

    return render(request, 'home.html', {'types': types,
                                         'cases': as_cases,
                                         'contacts': as_contacts,
                                         'outbreaks': outbreaks})


@login_required(login_url='/accounts/login/')
def cases(request):
    cs_assigns = Assignments.objects.filter(case__case_id__gte=0)
    cs_cases = Cases.objects.all()
    phones = PersonPhoneJoin.objects.all()
    today = datetime.today().date()
    symptoms = CaseSxJoin.objects.all()
    cs_sx_logs = SxLogJoin.objects.all()
    logs = CaseLogJoin.objects.all()
    cs_contacts = CaseContactJoin.objects.all()
    ct_type = 'C'
    cs_name = 'Cases'

    return render(request, 'case-list.html', {'today': today,
                                              'phones': phones,
                                              'assigns': cs_assigns,
                                              'cases': cs_cases,
                                              'sxLogs': cs_sx_logs,
                                              'logs': logs,
                                              'symptoms': symptoms,
                                              'contacts': cs_contacts,
                                              'type': ct_type,
                                              'name': cs_name,})


@login_required(login_url='/accounts/login/')
def contacts(request):
    ct_cases = Contacts.objects.all()
    ct_type = 'CT'
    ct_name = 'Contacts'

    return render(request, 'case-list.html', {'cases': ct_cases,
                                              'type': ct_type,
                                              'name': ct_name,})


@login_required(login_url='/accounts/login/')
def info(request, cttype, pid):
    if cttype == "C":
        data = Cases.objects.filter(case_id=pid).first()
        in_contacts = CaseContactJoin.objects.filter(case_id=pid)
        sxs = CaseSxJoin.objects.filter(case_id=pid)
        logs = CaseLogJoin.objects.filter(case_id=pid)
        in_name = 'Case'
        last_exposure = None
        contacts_logs = ContactLogJoin.objects.\
            filter(contact_id__in=in_contacts.values('contact_id'))
        ct_symptoms = ContactSxJoin.objects.filter(case_id__in=in_contacts.values('contact_id'))
        ct_logs = ContactLogJoin.objects.filter(contact_id__in=in_contacts.values('contact_id'))
    elif cttype == "CT":
        data = Contacts.objects.filter(contact_id=pid).first()
        in_contacts = CaseContactJoin.objects.filter(contact_id=pid)
        sxs = ContactSxJoin.objects.filter(case_id=pid)
        logs = ContactLogJoin.objects.filter(contact_id=pid)
        in_name = 'Contact'
        last_exposure = data.last_exposure
        contacts_logs = CaseLogJoin.objects.\
            filter(case_id__in=in_contacts.values('case_id'))
        ct_symptoms = CaseSxJoin.objects.filter(case_id__in=in_contacts.values('case_id'))
        ct_logs = CaseLogJoin.objects.filter(case_id__in=in_contacts.values('case_id'))
    else:
        raise Http404("Invalid case type")

    if data is None:
        raise Http404("No data for this case exists")

    sx_ids = sxs.values('sx_id')
    # print(sx_ids)
    symptoms = SxLogJoin.objects.filter(sx_id__in=sx_ids)
    ct_symptoms_details = SxLogJoin.objects.filter(sx_id__in=ct_symptoms.values('sx_id'))
    # print(symptoms)
    sx_logs = SxLog.objects.filter(log_id__in=symptoms)
    ct_logs_details = TraceLogs.objects.filter(log_id__in=ct_logs.values('log_id'))
    person_id = data.person_id
    # print(person_id)
    phones = PersonPhoneJoin.objects.filter(person_id=person_id)
    # print(phones)
    today = datetime.today().date()
    qt_release = None
    tent_rel_calc = None

    if sx_logs is not None:
        first_sx = datetime.today().date()
        for sx_log in sx_logs:
            first_sx = min(first_sx, sx_log.start)
    else:
        first_sx = None
    # print(symptoms)

    if first_sx is not None:
        tent_rel_calc = first_sx + timedelta(days=10)
    if last_exposure is not None:
        qt_release = last_exposure + timedelta(days=14)

    return render(request, 'tracing-info.html', {'case': data,
                                                 'contacts': in_contacts,
                                                 'symptoms': symptoms,
                                                 'logs': logs,
                                                 'type': cttype,
                                                 'name': in_name,
                                                 'phones': phones,
                                                 'first_sx': first_sx,
                                                 'tent_rel': tent_rel_calc,
                                                 'qt_rel': qt_release,
                                                 'contacts_logs': contacts_logs,
                                                 'ct_symptoms_details': ct_symptoms_details,
                                                 'ct_symptoms': ct_symptoms,
                                                 'ct_logs': ct_logs,
                                                 'ct_logs_details': ct_logs_details,
                                                 'today': today})
