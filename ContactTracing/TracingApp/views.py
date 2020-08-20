from django.shortcuts import render, redirect, get_object_or_404
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
        in_contacts = CaseContactJoin.objects.filter(case=data)
        sxs = CaseSxJoin.objects.filter(case=data).first()
        logs = CaseLogJoin.objects.filter(case=data).first()
        in_name = 'Case'
        last_exposure = None
        contacts_logs = ContactLogJoin.objects.\
            filter(contact__in=in_contacts.values('contact_id'))
        ct_symptoms = ContactSxJoin.objects.filter(case_id__in=in_contacts.values('contact_id'))
        ct_logs = ContactLogJoin.objects.filter(contact_id__in=in_contacts.values('contact_id'))
    elif cttype == "CT":
        data = Contacts.objects.filter(contact_id=pid).first()
        in_contacts = CaseContactJoin.objects.filter(contact=data)
        sxs = ContactSxJoin.objects.filter(case=data).first()
        logs = ContactLogJoin.objects.filter(contact=data).first()
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

    if sxs:
        sx_ids = sxs.values('sx_id')
        symptoms = SxLogJoin.objects.filter(sx_id__in=sx_ids)
        sx_logs = SxLog.objects.filter(log_id__in=symptoms)
    else:
        sx_ids = None
        symptoms = None
        sx_logs = None
    # print(sx_ids)

    ct_symptoms_details = SxLogJoin.objects.filter(sx_id__in=ct_symptoms.values('sx_id'))
    # print(symptoms)

    ct_logs_details = TraceLogs.objects.filter(log_id__in=ct_logs.values('log_id'))
    person_id = data.person_id
    # print(person_id)
    phones = PersonPhoneJoin.objects.filter(person_id=person_id)
    # print(phones)
    today = datetime.date.today()
    qt_release = None
    tent_rel_calc = None

    addresses = PersonAddressJoin.objects.filter(person_id=person_id)

    if sx_logs is not None:
        print("This should be none for this test")
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
                                                 'addresses': addresses,
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


@login_required(login_url='/accounts/login/')
def new_person(request):
    person = Persons()
    address = Addresses()
    phone = Phones()

    PersonAddressFormSet = inlineformset_factory(Persons, PersonAddressJoin, exclude=(), can_delete=False, extra=1)
    PersonPhoneFormSet = inlineformset_factory(Persons, PersonPhoneJoin, exclude=(), can_delete=False, extra=1)

    if request.method == "POST":
        personform = NewPersonForm(request.POST, instance=person)
        addressform = NewAddressForm(request.POST, instance=address)
        phoneform = NewPhoneNumberForm(request.POST, instance=phone)

        if personform.is_valid() and addressform.is_valid() and phoneform.is_valid():
            old_address = addressform.cleaned_data['address_id']
            if old_address:
                new_address = Addresses.objects.get(address_id=old_address)
            else:
                new_address = addressform.save()

            old_phone = phoneform.cleaned_data['phone_id']
            if old_address:
                new_phone = Phones.objects.get(phone_id=old_phone)
            else:
                new_phone = phoneform.save()

            new_person = personform.save()

            personaddress = PersonAddressJoin(person=new_person, address=new_address)
            personphone = PersonPhoneJoin(person=new_person, phone=new_phone)

            personaddress.save()
            personphone.save()

            return redirect('assignments')

    else:
        personform = NewPersonForm(instance=person)
        addressform = NewAddressForm(instance=address)
        phoneform = NewPhoneNumberForm(instance=phone)

    return render(request, 'test-person.html', {'personform': personform,
                                                'addressform': addressform,
                                                'phoneform': phoneform,
                                                })


@login_required(login_url='/accounts/login/')
def new_case(request):
    person = Persons()
    address = Addresses()
    phone = Phones()
    assignment = Assignments()
    test = Tests()
    # test.logged_date = datetime.date.today()
    # print(test.logged_date)

    if request.method == "POST":

        print("POST")
        personform = NewPersonForm(request.POST, instance=person)
        addressform = NewAddressForm(request.POST, instance=address)
        phoneform = NewPhoneNumberForm(request.POST, instance=phone)
        assignform = NewAssignment(request.POST, instance=assignment, initial={'status': False})

        # today = datetime.date.today()
        testform = NewTest(request.user, request.POST, instance=test)
        # testform.logged_date = datetime.date.today()

        assignform_valid = assignform.is_valid()
        testform_valid = testform.is_valid()
        personform_valid = personform.is_valid()
        addressform_valid = addressform.is_valid()
        phoneform_valid = phoneform.is_valid()

        print('Assign: %s || Test: %s || Person: %s || Address: %s || Phone: %s' % (assignform_valid, testform_valid, personform_valid, addressform_valid, phoneform_valid))
        # print(testform.cleaned_data['logged_date'])

        if personform.is_valid() and addressform.is_valid() and phoneform.is_valid() and assignform.is_valid() and testform.is_valid():
            print("validation testing")
            try:
                old_address = addressform.cleaned_data['address_id']
                new_address = Addresses.objects.get(address_id=old_address)
            except KeyError:
                new_address = addressform.save()

            try:
                old_phone = phoneform.cleaned_data['phone_id']
                new_phone = Phones.objects.get(phone_id=old_phone)
            except KeyError:
                new_phone = phoneform.save()

            print("before test save")
            new_test = testform.save()
            print("saved test")
            new_person = personform.save()
            print("saved person")

            personaddress = PersonAddressJoin(person=new_person, address=new_address)
            personphone = PersonPhoneJoin(person=new_person, phone=new_phone)

            personaddress.save()
            personphone.save()
            print("saved personphone")

            needs_invest_status = Statuses.objects.get(status_id=1)
            newcase = Cases(person=new_person, test=new_test, active=True, status=needs_invest_status)
            print("made newcase")

            newassign = Assignments(case=newcase,
                                    assign_type=assignform.cleaned_data['assign_type'],
                                    status=assignform.cleaned_data['status'],
                                    user=assignform.cleaned_data['user'])
            print("made newassign")

            new_person.save()
            new_test.save()
            newcase.save()
            newassign.save()
            assignform.save()

            return redirect('assignments')

    else:
        personform = NewPersonForm(instance=person)
        addressform = NewAddressForm(instance=address)
        phoneform = NewPhoneNumberForm(instance=phone)
        assignform = NewAssignment(instance=assignment)
        testform = NewTest(request.user, instance=test)

    return render(request, 'add-new-case.html', {'personform': personform,
                                                 'addressform': addressform,
                                                 'phoneform': phoneform,
                                                 'assignform': assignform,
                                                 'testform': testform,
                                                 })


@login_required(login_url='/accounts/login/')
def case_investigation(request, cttype, pid):
    if cttype != 'C':
        raise Http404("Invalid Case Type")

    case = get_object_or_404(Cases, case_id=pid)
    person = get_object_or_404(Persons, person_id=case.person_id)
    test = get_object_or_404(Tests, test_id=case.test_id)
    log = TraceLogs()
    addressesJoins = PersonAddressJoin.objects.filter(person=person)
    addresses = Addresses.objects.filter(address_id__in=addressesJoins.values('address_id'))

    addressformset = modelformset_factory(Addresses,  form=NewAddressForm, extra=0)
    phoneformset = modelformset_factory(Phones, form=NewPhoneNumberForm, extra=0)

    symptomformset = modelformset_factory(Symptoms, form=SymptomForm, extra=1)
    symptomlogformset = modelformset_factory(SxLog, form=SymptomLogForm, extra=1)
    symptomloghelper = SymptomLogSetHelper()

    if request.method == "POST":
        print("POST")

        caseform = CaseForm(request.POST, instance=case)
        personform = NewPersonForm(request.POST, instance=person)
        testform = NewTest(request.user, request.POST, instance=test)
        logform = TraceLogForm(request.user, request.POST, instance=log)

        queryset = PersonAddressJoin.objects.filter(person_id=case.person_id)
        addressforms = addressformset(request.POST, queryset=Addresses.objects.filter(address_id__in=queryset.values('address_id')))

        phonequery = PersonPhoneJoin.objects.filter(person_id=case.person_id)
        phoneforms = phoneformset(request.POST, queryset=Phones.objects.filter(phone_id__in=phonequery.values('phone_id')))
        symptomforms = symptomformset(request.POST)
        symptomlogforms = symptomlogformset(request.user, request.POST)

        if caseform.is_valid() \
                and personform.is_valid()\
                and testform.is_valid()\
                and addressforms.is_valid()\
                and phoneforms.is_valid() \
                and symptomforms.is_valid():

            this_person = personform.save(commit=False)

            for addressform in addressforms:
                if addressform.is_valid():
                    this_address = addressform.save(commit=False)
                    person_address = PersonAddressJoin(person=this_person, address=this_address)
                    person_address.save()
                    this_address.save()

            for phoneform in phoneforms:
                if phoneform.is_valid():
                    this_phone = phoneform.save(commit=False)
                    person_phone = PersonPhoneJoin(person=this_person, phone=this_phone)
                    person_phone.save()
                    this_phone.save()

            this_test = testform.save(commit=False)

            caseform.cleaned_data['test'] = this_test
            caseform.cleaned_data['person'] = this_person
            this_case = caseform.save(commit=False)

            for symptomlogform in symptomlogforms:
                if symptomlogform.is_valid():
                    symptomlogform.cleaned_data['case'] = this_case
                    symptomlogform.save()

            this_test.save()
            this_person.save()
            this_case.save()

            return redirect('assignments')

    else:
        personform = NewPersonForm(instance=person)
        testform = NewTest(request.user, instance=test)

        queryset = PersonAddressJoin.objects.filter(person_id=case.person_id)
        addressforms = addressformset(queryset=Addresses.objects.filter(address_id__in=queryset.values('address_id')))
        phonequery = PersonPhoneJoin.objects.filter(person_id=case.person_id)
        phoneforms = phoneformset(queryset=Phones.objects.filter(phone_id__in=phonequery.values('phone_id')))
        caseform = CaseForm(instance=case)
        logform = TraceLogForm(request.user, instance=log)

        symptomforms = symptomformset(queryset=Symptoms.objects.none())
        symptomlogforms = symptomlogformset(request.user, queryset=SxLog.objects.none())

    return render(request, 'case edit/case-investigation.html', {'caseform': caseform,
                                                                 'personform': personform,
                                                                 'addressforms': addressforms,
                                                                 'phoneforms': phoneforms,
                                                                 'testform': testform,
                                                                 'symptomforms': symptomforms,
                                                                 'symptomlogforms': symptomlogforms,
                                                                 'symptomloghelper': symptomloghelper,
                                                                 'logform': logform,
                                                                 })
