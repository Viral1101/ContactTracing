from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404
from .models import *
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from .forms import CaseForm
from django.views.generic.edit import FormView
from django.utils.decorators import method_decorator
from django.forms import inlineformset_factory, modelformset_factory
from .forms import *

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
    # cs_assigns = Assignments.objects.filter(case__case_id__gte=0)
    cs_cases = Cases.objects.all()
    # phones = PersonPhoneJoin.objects.all()
    today = datetime.date.today()
    # symptoms = CaseSxJoin.objects.all()
    # cs_sx_logs = SxLogJoin.objects.all()
    # logs = CaseLogJoin.objects.all()
    # cs_contacts = CaseContactJoin.objects.all()
    ct_type = 'C'
    cs_name = 'Cases'

    return render(request, 'case-list.html', {'today': today,
                                              # 'phones': phones,
                                              # 'assigns': cs_assigns,
                                              'cases': cs_cases,
                                              # 'sxLogs': cs_sx_logs,
                                              # 'logs': logs,
                                              # 'symptoms': symptoms,
                                              # 'contacts': cs_contacts,
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
    today = datetime.date.today()
    qt_release = None
    tent_rel_calc = None

    if sx_logs is not None:
        first_sx = datetime.date.today()
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


# @method_decorator(login_required, name='dispatch')
# class NewCaseForm(FormView):
#     form_class = CaseForm
#
#     template_name = 'add-new-case.html'
#
#     def dispatch(self, *args, **kwargs):
#         return super().dispatch(*args, **kwargs)
#
#     def form_valid(self, form):
#         # This method is called when valid form data has been POSTed.
#         # It should return an HttpResponse.
#
#         # perform a action here
#         print(form.cleaned_data)
#         return super().form_valid(form)


def new_person(request):

    person = Persons()
    address = Addresses()
    phone = Phones()
    personaddress = PersonAddressJoin()
    personphone = PersonPhoneJoin()

    # PersonAddressFormSet = inlineformset_factory(Persons, PersonAddressJoin, exclude=(), can_delete=False, extra=1)
    # AddressPersonFormset = inlineformset_factory(Addresses, PersonAddressJoin, exclude=(), can_delete=False, extra=1)
    # PhoneFormSet = inlineformset_factory(Persons, PersonPhoneJoin, exclude=(), can_delete=False, extra=1)

    if request.method == "POST":
        personform = NewPersonForm(request.POST, instance=person)
        addressform = NewAddressForm(request.POST, instance=address)
        phoneform = NewPhoneNumberForm(request.POST, instance=phone)
        # personaddressformset = PersonAddressFormSet(request.POST, request.FILES, instance=person)
        # addresspersonformset = AddressPersonFormset(request.POST, request.FILES, instance=address)
        # personphoneformset = PersonPhoneFormSet(request.POST, request.FILES, instance=person)

        if personform.is_valid() and addressform.is_valid() and phoneform.is_valid():
            personaddress.address = personform.instance()
            personaddress.person = addressform.instance()
            personphone.person = personform.instance()
            personphone.phone = phoneform.instance()

            personform.save()
            addressform.save()
            phoneform.save()
            personaddress.save()
            personphone.save()

            if '_save' in request.POST:
                return HttpResponseRedirect('/TracingApp/assigns')

    else:
        personform = NewPersonForm(instance=person)
        addressform = NewAddressForm(instance=address)
        phoneform = NewPhoneNumberForm(instance=phone)
        # personaddressformset = PersonAddressFormSet(instance=person)
        # addresspersonformset = AddressPersonFormset(instance=address)
        # personphoneformset = PersonPhoneFormSet(instance=person)

    return render(request, 'test-person.html', {'personform': personform,
                                                'addressform': addressform,
                                                'phoneform': phoneform,
                                                # 'personaddressformset': personaddressformset,
                                                # 'addresspersonformset': addresspersonformset,
                                                # 'phonelink': personphoneformset,
                                                })


def new_case_test(request):

    person = Persons()
    # PersonFormSet = NewPersonForm(instance=person)

    # PersonAddressFormset = inlineformset_factory(Persons, PersonAddressJoin, fields=())
    AddressFormSet = inlineformset_factory(Addresses, PersonAddressJoin, form=NewAddressForm, extra=1, can_delete=False)
    # PersonPhoneFormSet = inlineformset_factory(Phones, PersonPhoneJoin, fields=())
    # PhonePersonsFormSet = inlineformset_factory(Persons, PersonPhoneJoin, fields=())
    # PhoneFormSet = modelformset_factory(Phones, form=NewPhoneNumberForm)
    PersonFormSet = inlineformset_factory(Persons, form=NewPersonForm)

    # print(AddressFormSet)

    if request.method == 'POST':
        address_formset = AddressFormSet(request.POST, request.FILES, prefix='addresses')
        # person_formset = PersonFormSet(request.POST, prefix='persons')
        # person_address_formset = PersonAddressFormset(request.POST, request.FILES, prefix='persons_addresses')
        # phone_formset = PhoneFormSet(request.POST, request.FILES, prefix='phones')
        # personphone_formset = PersonPhoneFormSet(request.POST, request.FILES, prefix='personphones')
        # phoneperson_formset = PhonePersonsFormSet(request.POST, request.FILES, prefix='phonepersons')
        # if address_formset.is_valid() and person_formset.is_valid() and phone_formset.is_valid() and personphone_formset.is_valid() and phonepersion_formset.is_valid():
        if address_formset.is_valid():
            print("All valid, time to do something")
            # formset.save()
            # do something.

    else:
        address_formset = AddressFormSet(queryset=PersonAddressJoin.objects.none(), prefix='addresses')
        # person_formset = PersonFormSet(queryset=Persons.objects.none(), prefix='persons')
        # person_address_formset = PersonAddressFormset(request.POST, request.FILES, prefix='persons_addresses')
        # phone_formset = PhoneFormSet(queryset=Phones.objects.none(), prefix='phones')
        # personphone_formset = PersonPhoneFormSet(prefix='personphones')
        # phonepersion_formset = PhonePersonsFormSet(prefix='phonepersons')

    # print(address_formset)

    return render(request, 'test-person.html', {'address_formset': address_formset,
                                                # 'person_formset': person_formset,
                                                # 'person_address_formset': person_address_formset,
                                                   # 'phone_formset': phone_formset,
                                                   # 'personphone_formset': personphone_formset,
                                                   # 'phonepersion_formset': phonepersion_formset,
                                                   })
