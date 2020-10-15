from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from .models import *
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from .forms import CaseForm
from django.views.generic.edit import FormView
from django.utils.decorators import method_decorator
from django.forms import inlineformset_factory, modelformset_factory, formset_factory
from .forms import *
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Q

# Create your views here.


@login_required(login_url='/accounts/login/')
def index(request):
    # return HttpResponse("This is the index.")
    return assigns(request)


@login_required(login_url='/accounts/login/')
def assigns(request):
    types = AssignmentType.objects.all()
    current_user = request.user.id
    assignments = Assignments.objects.filter(user__id=current_user).order_by('assign_type')
    as_cases = assignments.filter(case__case_id__gte=0)
    as_contacts = assignments.filter(contact__contact_id__gte=0)
    outbreaks = assignments.filter(outbreak__outbreak_id__gte=0)

    print(assignments)

    return render(request, 'home.html', {'types': types,
                                         'cases': as_cases,
                                         'contacts': as_contacts,
                                         'outbreaks': outbreaks})


@login_required(login_url='/accounts/login/')
def cases(request):
    cs_cases = Cases.objects.all()
    # phones = PersonPhoneJoin.objects.all()
    today = datetime.date.today()
    # symptoms = CaseSxJoin.objects.all()
    # cs_sx_logs = SxLogJoin.objects.all()
    # logs = CaseLogJoin.objects.all()
    # cs_contacts = CaseContactJoin.objects.all()
    ct_type = 'C'
    cs_name = 'Cases'
    cs_assigns = Assignments.objects.filter(case__in=cs_cases, status=1)

    print(len(cs_assigns))

    return render(request, 'case-list.html', {'today': today,
                                              # 'phones': phones,
                                              'assigns': cs_assigns,
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
    cs_assigns = Assignments.objects.filter(contact__in=ct_cases, status=1)

    return render(request, 'case-list.html', {'cases': ct_cases,
                                              'type': ct_type,
                                              'name': ct_name,
                                              'assigns': cs_assigns,})


@login_required(login_url='/accounts/login/')
def info(request, cttype, pid):

    pending = AssignmentStatus.objects.get(status_id=1)

    if cttype == "C":
        data = Cases.objects.get(case_id=pid)
        in_contacts = CaseContactJoin.objects.filter(case=data)
        sxs = CaseSxJoin.objects.filter(case=data)
        logs = CaseLogJoin.objects.filter(case=data)
        in_name = 'Case'
        last_exposure = None
        contacts_logs = ContactLogJoin.objects.\
            filter(contact__in=in_contacts.values('contact_id'))
        ct_symptoms = ContactSxJoin.objects.filter(case_id__in=in_contacts.values('contact_id'))
        ct_logs = ContactLogJoin.objects.filter(contact_id__in=in_contacts.values('contact_id'))
        testquery = CaseTestJoin.objects.filter(case_id=data)
        upstream_cases = CaseLinks.objects.filter(developed_case=data)
        downstream_cases = CaseLinks.objects.filter(exposing_case=data)
        assigned = Assignments.objects.filter(case_id=pid, status=pending).first()
    elif cttype == "CT":
        data = Contacts.objects.filter(contact_id=pid).first()
        in_contacts = CaseContactJoin.objects.filter(contact=data)
        sxs = ContactSxJoin.objects.filter(case=data)
        logs = ContactLogJoin.objects.filter(contact=data)
        in_name = 'Contact'
        last_exposure = data.last_exposure
        contacts_logs = CaseLogJoin.objects.\
            filter(case_id__in=in_contacts.values('case_id'))
        ct_symptoms = CaseSxJoin.objects.filter(case_id__in=in_contacts.values('case_id'))
        ct_logs = CaseLogJoin.objects.filter(case_id__in=in_contacts.values('case_id'))
        # print(ct_logs.values('case_id'))
        testquery = ContactTestJoin.objects.filter(contact_id=data)
        upstream_cases = None
        downstream_cases = None
        assigned = Assignments.objects.filter(contact_id=pid, status=pending).first()
    else:
        raise Http404("Invalid case type")

    if data is None:
        raise Http404("No data for this case exists")

    if sxs:
        # print(sxs)
        sx_ids = sxs.values('sx_id')
        # symptoms = SxLogJoin.objects.filter(sx_id__in=sx_ids)
        # sx_logs = SxLog.objects.filter(log_id__in=symptoms)
        symptoms = SxLog.objects.filter(log_id__in=sx_ids).order_by('symptom', 'rec_date')
        sx_logs = symptoms
    else:
        sx_ids = None
        symptoms = None
        sx_logs = None
    # print(sx_ids)

    testforms = Tests.objects.filter(test_id__in=testquery.values('test_id'))

    ct_symptoms_details = SxLogJoin.objects.filter(sx_id__in=ct_symptoms.values('sx_id'))
    # print(symptoms)

    ct_logs_details = TraceLogs.objects.filter(log_id__in=ct_logs.values('log_id'))
    person_id = data.person_id
    # print(person_id)
    phones = PersonPhoneJoin.objects.filter(person_id=person_id)
    # print(phones)
    emails = PersonEmailJoin.objects.filter(person_id=person_id)
    today = datetime.date.today()
    qt_release = None
    tent_rel_calc = None

    followup_day = datetime.date.today() - timedelta(days=7)

    addresses = PersonAddressJoin.objects.filter(person_id=person_id)

    if symptoms is not None:
        # print("This should be none for this test")
        first_sx = datetime.date.today()
        for symptom in symptoms:
            if symptom.start is not None:
                first_sx = min(first_sx, symptom.start)
    else:
        first_sx = None
    # print(symptoms)

    if first_sx is not None:
        tent_rel_calc = first_sx + timedelta(days=10)
    if last_exposure is not None:
        qt_release = last_exposure + timedelta(days=14)

    user = AuthUser.objects.filter(id=request.user.id).first()

    if request.method == 'POST':
        if 'assign_to_me' in request.POST:
            pending_status = AssignmentStatus.objects.get(status_id=1)
            # print('save_exit')
            if cttype == 'C':
                this_assign = Assignments(user=user, case_id=pid, status=pending_status)
            elif cttype == 'CT':
                this_assign = Assignments(user=user, contact_id=pid, status=pending_status)
            else:
                this_assign = Assignments(user=user, outbreak_id=pid, status=pending_status)
            this_assign.save()
            return redirect('info', cttype=cttype, pid=pid)
        elif 'drop_assignment' in request.POST:
            dropped_status = AssignmentStatus.objects.get(status_id=3)
            assigned.status = dropped_status
            assigned.date_done = datetime.date.today()
            assigned.save()
            return redirect('assignments')
        else:
            return redirect('assignments')

    print(assigned)

    if assigned is not None:
        if assigned.user is not None:
            assigned_to_this_user = assigned.user.id == request.user.id
        else:
            assigned_to_this_user = False
    else:
        assigned_to_this_user = False

    return render(request, 'info/tracing-info.html', {'case': data,
                                                      'contacts': in_contacts,
                                                      'symptoms': sx_logs,
                                                      'logs': logs,
                                                      'type': cttype,
                                                      'name': in_name,
                                                      'addresses': addresses,
                                                      'phones': phones,
                                                      'emails': emails,
                                                      'first_sx': first_sx,
                                                      'tent_rel': tent_rel_calc,
                                                      'qt_rel': qt_release,
                                                      'contacts_logs': contacts_logs,
                                                      'ct_symptoms_details': ct_symptoms_details,
                                                      'ct_symptoms': ct_symptoms,
                                                      'ct_logs': ct_logs,
                                                      'ct_logs_details': ct_logs_details,
                                                      'testforms': testforms,
                                                      'today': today,
                                                      'followup_day': followup_day,
                                                      'upstream_cases': upstream_cases,
                                                      'downstream_cases': downstream_cases,
                                                      'assigned': assigned,
                                                      'assigned_to_this_user': assigned_to_this_user,
                                                      })


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
    user = AuthUser.objects.get(id=request.user.id)
    # test.logged_date = datetime.date.today()
    # print(test.logged_date)

    pending_status = AssignmentStatus.objects.get(status_id=1)

    if request.method == "POST":

        # print("POST")
        personform = NewPersonForm(request.POST, instance=person)
        addressform = NewAddressForm(request.POST, instance=address)
        phoneform = NewPhoneNumberForm(request.POST, instance=phone)
        assignform = NewAssignment(request.POST, instance=assignment, initial={'status': AssignmentStatus.objects.get(status_id=1),
                                                                               'assign_type': 1})

        # today = datetime.date.today()
        testform = NewTest(request.POST, instance=test)
        # testform.logged_date = datetime.date.today()

        assignform_valid = assignform.is_valid()
        testform_valid = testform.is_valid()
        personform_valid = personform.is_valid()
        addressform_valid = addressform.is_valid()
        phoneform_valid = phoneform.is_valid()

        print('Assign: %s || Test: %s || Person: %s || Address: %s || Phone: %s' %
              (assignform_valid, testform_valid, personform_valid, addressform_valid, phoneform_valid))
        print(testform.cleaned_data['logged_date'])

        print(assignform.errors)

        if personform.is_valid()\
                and addressform.is_valid()\
                and phoneform.is_valid()\
                and assignform.is_valid()\
                and testform.is_valid():
            # print("validation testing")
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

            # print("before test save")
            new_test = testform.save(commit=False)
            new_test.user = user
            new_test.save()
            # print("saved test")
            new_person = personform.save()
            # print("saved person")

            personaddress = PersonAddressJoin(person=new_person, address=new_address)
            personphone = PersonPhoneJoin(person=new_person, phone=new_phone)

            personaddress.save()
            personphone.save()
            # print("saved personphone")

            needs_invest_status = Statuses.objects.get(status_id=1)
            newcase = Cases(person=new_person, active=True, status=needs_invest_status)
            # print("made newcase")

            newassign = Assignments(case=newcase,
                                    assign_type=assignform.cleaned_data['assign_type'],
                                    status=pending_status,
                                    user=assignform.cleaned_data['user'])
            # print("made newassign")

            # new_person.save()
            # new_test.save()
            newcase.save()
            newassign.save()
            # assignform.save()

            case_test = CaseTestJoin(case=newcase, test=test)
            case_test.save()

            messages.success(request, 'Case C%s created for %s %s' % (newcase.case_id, new_person.first, new_person.last))
            return redirect('assignments')

    else:
        personform = NewPersonForm(instance=person)
        addressform = NewAddressForm(instance=address, initial={'state':'MO'})
        phoneform = NewPhoneNumberForm(instance=phone)
        assignform = NewAssignment(instance=assignment, initial={'status': pending_status, 'assign_type': 1})
        testform = NewTest(instance=test)

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
    test_1 = CaseTestJoin.objects.filter(case_id=pid)
    test = Tests.objects.filter(test_id__in=test_1.values('test'))
    if len(test) > 0:
        test_extra = 0
    else:
        test_extra = 1
    user = AuthUser.objects.get(id=request.user.id)
    log = TraceLogs()
    # addressesJoins = PersonAddressJoin.objects.filter(person=person)
    # addresses = Addresses.objects.filter(address_id__in=addressesJoi
    # ns.values('address_id'))

    # print(test)

    AddressFormSet = modelformset_factory(Addresses, form=AddressesForm, extra=0)
    PhoneFormSet = modelformset_factory(Phones, form=PhoneForm, extra=0)

    NewTestFormSet = modelformset_factory(Tests, form=NewTest, extra=test_extra) #for adding new tests if needed
    EmailFormSet = modelformset_factory(Emails, form=EmailForm, extra=1)

    SymptomFormSet = modelformset_factory(Symptoms, form=SymptomForm, extra=1)
    SymptomLogFormSet = modelformset_factory(SxLog, form=NewSymptomLogForm, extra=1)
    symptomloghelper = SymptomLogSetHelper()

    addressformhelper = AddressesFormHelper()
    emailformhelper = EmailFormHelper()
    phoneformhelper = PhoneFormHelper()
    testformhelper = NewTestFormHelper()

    person_address_query = PersonAddressJoin.objects.filter(person_id=case.person_id)
    addressquery = Addresses.objects.filter(address_id__in=person_address_query.values('address_id'))

    person_phone_query = PersonPhoneJoin.objects.filter(person_id=case.person_id)
    phone_query = Phones.objects.filter(phone_id__in=person_phone_query.values('phone_id'))

    person_email_query = PersonEmailJoin.objects.filter(person_id=case.person_id)
    emailquery = Emails.objects.filter(email_id__in=person_email_query.values('email_id'))

    case_sx_query = CaseSxJoin.objects.filter(case=case)
    symptom_query = SxLog.objects.filter(symptom_id__in=case_sx_query.values('sx_id'))

    if request.method == "POST":

        caseform = InvestigationCaseForm(request.POST, instance=case)
        personform = PersonForm(request.POST, instance=person)
        testforms = NewTestFormSet(request.POST, queryset=test, prefix='new_test')
        logform = NewTraceLogForm(user, request.POST, instance=log)

        addressforms = AddressFormSet(request.POST, prefix='address', queryset=addressquery)
        emailforms = EmailFormSet(request.POST, prefix='email', queryset=emailquery)
        # new_testforms = NewTestFormSet(request.POST, prefix='new_test')

        # phone_query = PersonPhoneJoin.objects.filter(person_id=case.person_id)
        phoneforms = PhoneFormSet(request.POST, prefix='phone', queryset=phone_query)
        symptomforms = SymptomFormSet(request.POST, prefix='symptom')
        symptomlogforms = SymptomLogFormSet(request.POST, prefix='sxlog',
                                            queryset=symptom_query)

        for symptomlogform in symptomlogforms:
            symptomlogform.user = user

        # logform.user = user
            # symptomlogform.rec_date = datetime.date.today()

        print("Case: %s | Person: %s | Address: %s | Phone: %s | Email: %s | Test: %s | Log: %s | Sx: %s" %
              (caseform.is_valid(),
               personform.is_valid(),
               addressforms.is_valid(),
               emailforms.is_valid(),
               phoneforms.is_valid(),
               testforms.is_valid(),
               logform.is_valid(),
               symptomlogforms.is_valid()))

        if caseform.is_valid() \
                and personform.is_valid()\
                and testforms.is_valid()\
                and addressforms.is_valid()\
                and phoneforms.is_valid() \
                and emailforms.is_valid() \
                and logform.is_valid() \
                and symptomlogforms.is_valid():

            this_person = personform.save(commit=False)

            for addressform in addressforms:
                if addressform.is_valid():
                    this_address = addressform.save()
                    person_address, created = PersonAddressJoin.objects.get_or_create(person=this_person, address=this_address)
                    person_address.save()
                    # this_address.save()
            # print("address done")

            for phoneform in phoneforms:
                if phoneform.is_valid():
                    this_phone = phoneform.save()
                    person_phone, created2 = PersonPhoneJoin.objects.get_or_create(person=this_person, phone=this_phone)
                    person_phone.save()
                    # this_phone.save()
            # print("phone done")

            for emailform in emailforms:
                if emailform.is_valid():
                    this_email = emailform.save()
                    person_email, created4 = PersonEmailJoin.objects.get_or_create(person=this_person, email=this_email)
                    person_email.save()
            # print("email done")

            # this_test = testform.save(commit=False)

            # caseform.cleaned_data['test'] = this_test
            caseform.cleaned_data['person'] = this_person
            # print("1")

            this_case = caseform.save(commit=False)
            this_log = logform.save(commit=False)
            this_log.user = user
            this_log.save()
            # print("2")
            # print(this_log)

            case_log, log_created = CaseLogJoin.objects.get_or_create(case=this_case, log=this_log)
            case_log.save()
            # print("3")
            for symptomlogform in symptomlogforms:
                if symptomlogform.is_valid():
                    try:
                        if symptomlogform.cleaned_data['symptom']:
                            this_symptom = symptomlogform.save(commit=False)
                            this_symptom.user = user
                            this_symptom.save()
                            case_sx, created3 = CaseSxJoin.objects.get_or_create(case=this_case, sx=this_symptom)
                            case_sx.save()
                    except KeyError:
                        #     No Symptoms to record
                        pass
            # print("symptom done")

            # this_test.save()
            this_person.save()
            this_case.save()

            print("up to the test section")
            if testforms.has_changed():
                print("formset has changed")
                for testform in testforms:
                    if testform.has_changed():
                        print("form has changed")
                        if testform.is_valid():
                            print("form is valid")
                            this_test = testform.save(commit=False)
                            this_test.user = user
                            this_test.logged_date = datetime.date.today()
                            this_test.save()
                            case_test, case_test_ctd = CaseTestJoin.objects.get_or_create(case=this_case, test=this_test)
                            if case_test_ctd:
                                case_test.save()

            # Mark the assignment as done with the date

            pending = AssignmentStatus.objects.get(status_id=1)
            this_assignment = Assignments.objects.filter(case=this_case, user=user, status=pending).first()
            if this_assignment is not None:
                done_status = AssignmentStatus.objects.get(status_id=2)
                this_assignment.status = done_status
                this_assignment.date_done = datetime.date.today()
                this_assignment.save()

            if 'save_and_exit' in request.POST:
                # print('save_exit')
                return redirect('info', cttype=cttype, pid=pid)
            elif 'save_and_add_contacts' in request.POST:
                # print('save_contacts')
                return redirect('/TracingApp/add-contact/%s/%s' % (cttype, pid))
            else:
                return redirect('assignments')

    else:
        personform = PersonForm(instance=person)
        testforms = NewTestFormSet(queryset=test, prefix='new_test')
        # new_testforms = NewTestFormSet(user, queryset=Tests.objects.none(), prefix='new_test')

        addressforms = AddressFormSet(queryset=addressquery, prefix='address')
        emailforms = EmailFormSet(prefix='email', queryset=emailquery)
        # phonequery = PersonPhoneJoin.objects.filter(person_id=case.person_id)
        phoneforms = PhoneFormSet(queryset=phone_query, prefix='phone')
        caseform = InvestigationCaseForm(instance=case)
        logform = NewTraceLogForm(user, instance=log)

        symptomforms = SymptomFormSet(queryset=Symptoms.objects.none())
        symptomlogforms = SymptomLogFormSet(queryset=symptom_query, prefix='sxlog')

    return render(request, 'case edit/case-investigation.html', {'caseform': caseform,
                                                                 'personform': personform,
                                                                 'addressforms': addressforms,
                                                                 'addressformhelper': addressformhelper,
                                                                 'emailforms': emailforms,
                                                                 'emailformhelper': emailformhelper,
                                                                 'phoneforms': phoneforms,
                                                                 'phoneformhelper': phoneformhelper,
                                                                 'testforms': testforms,
                                                                 'testformhelper': testformhelper,
                                                                 # 'new_testforms': new_testforms,
                                                                 'symptomforms': symptomforms,
                                                                 'symptomlogforms': symptomlogforms,
                                                                 'symptomloghelper': symptomloghelper,
                                                                 'logform': logform,
                                                                 })


@login_required(login_url='/accounts/login/')
def add_contact(request, cttype, pid):

    if cttype != 'C':
        raise Http404("Invalid Case Type")

    case = get_object_or_404(Cases, case_id=pid)

    contact = Contacts()
    person = Persons()
    log = TraceLogs()
    AddressFormSet = modelformset_factory(Addresses, form=AddContactAddress, extra=1)
    PhoneFormSet = modelformset_factory(Phones, form=AddContactPhone, extra=1)
    SymptomLogFormSet = modelformset_factory(SxLog, form=NewSymptomLogForm, extra=1)
    EmailFormSet = modelformset_factory(Emails, form=AddContactEmailForm, extra=1)

    addressformhelper = AddContactAddressHelper()
    phoneformhelper = AddContactPhoneHelper()
    emailformhelper = AddContactEmailFormHelper()
    symptomloghelper = SymptomLogSetHelper()

    person_address_query = PersonAddressJoin.objects.none()
    addressquery = Addresses.objects.none()

    person_phone_query = PersonPhoneJoin.objects.none()
    phone_query = Phones.objects.none()
    email_query = Emails.objects.none()

    # case_sx_query = CaseSxJoin.objects.filter(case=case)
    symptom_query = SxLog.objects.none()

    user = AuthUser.objects.get(id=request.user.id)

    if request.method == 'POST':

        contactform = AddContactForm(request.POST, instance=contact)
        personform = PersonForm(request.POST, instance=person)
        logform = ContactTraceLogForm(user, request.POST, instance=log)
        relationform = AddCaseRelation(request.POST)
        usecasephoneform = AddCasePhoneForContact(request.POST)

        addressforms = AddressFormSet(request.POST, prefix='address')
        phoneforms = PhoneFormSet(request.POST, prefix='phone')
        emailforms = EmailFormSet(request.POST, prefix='email')

        symptomlogforms = SymptomLogFormSet(request.POST, prefix='sxlog')

        if 'cancel' in request.POST:
            return redirect('assignments')

        # print("Contact: %s | Person: %s | Address: %s | Phone: %s | Email: %s | Log: %s | Sx: %s" % (contactform.is_valid(),
        #                                                                                personform.is_valid(),
        #                                                                                addressforms.is_valid(),
        #                                                                                phoneforms.is_valid(),
        #                                                                                emailforms.is_valid(),
        #                                                                                              logform.is_valid(),
        #                                                                                symptomlogforms.is_valid()))

        # contactform.fields['person'] = person

        logform.user = AuthUser.objects.get(id=request.user.id)

        # for thing in addressforms:
            # print(thing.errors)

        if contactform.is_valid() \
                and personform.is_valid() \
                and relationform.is_valid() \
                and usecasephoneform.is_valid() \
                and emailforms.is_valid() \
                and addressforms.is_valid() \
                and phoneforms.is_valid() \
                and symptomlogforms.is_valid():

            this_person = personform.save()
            # print(contactform.cleaned_data)

            if contactform.cleaned_data['mark_as_contacted']:
                contactform.cleaned_data['last_follow'] = datetime.date.today()

            # print(contactform.cleaned_data)
            this_contact = contactform.save(commit=False)

            this_contact.person = this_person
            this_contact.save()
            # print(this_contact)
            # print(this_person)

            if contactform.cleaned_data['copy_case_notes']:
                case_log_query = CaseLogJoin.objects.filter(case=case).last()
                contact_log, ctd2 = ContactLogJoin.objects.get_or_create(contact=this_contact, log=case_log_query.log)
            else:
                # print(this_log.user)
                this_log = logform.save()
                contact_log, ctd2 = ContactLogJoin.objects.get_or_create(contact=this_contact, log=this_log)

            contact_log.save()

            relation = relationform.cleaned_data['relation_to_case']
            case_contact, ctd = CaseContactJoin.objects.get_or_create(case=case,
                                                                      contact=this_contact,
                                                                      relation_to_case=relation)
            case_contact.save()

            for addressform in addressforms:
                try:
                    if addressform.cleaned_data['use_case_address']:
                        case_address = PersonAddressJoin.objects.filter(person=case.person).first().address
                        person_address, created = PersonAddressJoin.objects.get_or_create(person=this_person,
                                                                                          address=case_address)
                        person_address.save()
                    else:
                        try:
                            if addressform.cleaned_data['street']:
                                this_address = addressform.save()
                                person_address, created = PersonAddressJoin.objects.get_or_create(person=this_person,
                                                                                                  address=this_address)
                                person_address.save()
                                # this_address.save()
                        except KeyError:
                            #     No address to record
                            pass
                except KeyError:
                    print("use_case_address threw KeyError")
                    try:
                        if addressform.cleaned_data['street']:
                            this_address = addressform.save()
                            person_address, created = PersonAddressJoin.objects.get_or_create(person=this_person,
                                                                                              address=this_address)
                            person_address.save()
                            # this_address.save()
                    except KeyError:
                        #     No address to record
                        pass

            if usecasephoneform.cleaned_data['use_case_phone']:
                case_phone = PersonPhoneJoin.objects.filter(person=case.person).first().phone
                person_phone, created2 = PersonPhoneJoin.objects.get_or_create(person=this_person, phone=case_phone)
                person_phone.save()

            for phoneform in phoneforms:
                # if phoneform.cleaned_data['use_case_phone']:
                #     case_phone = PersonPhoneJoin.objects.filter(person=case.person).first().phone
                #     person_phone, created2 = PersonPhoneJoin.objects.get_or_create(person=this_person, phone=case_phone)
                #     person_phone.save()
                if phoneform.is_valid():
                    this_phone = phoneform.save()
                    person_phone, created2 = PersonPhoneJoin.objects.get_or_create(person=this_person, phone=this_phone)
                    person_phone.save()
                    # this_phone.save()

            for emailform in emailforms:
                try:
                    if emailform.cleaned_data['use_case_email']:
                        case_email = PersonEmailJoin.objects.filter(person=case.person).first().email
                        person_email, created3 = PersonEmailJoin.objects.get_or_create(person=this_person, email=case_email)
                        person_email.save()
                    elif emailform.is_valid():
                        this_email = emailform.save()
                        person_email, created3 = PersonEmailJoin.objects.get_or_create(person=this_person, email=this_email)
                        person_email.save()
                        # this_phone.save()
                except KeyError:
                    pass

            for symptomlogform in symptomlogforms:
                if symptomlogform.is_valid():
                    try:
                        if symptomlogform.cleaned_data['symptom']:
                            this_symptom = symptomlogform.save(commit=False)
                            this_symptom.user = user
                            this_symptom.save()
                            case_sx, created3 = ContactSxJoin.objects.get_or_create(case=this_contact, sx=this_symptom)
                            case_sx.save()
                    except KeyError:
                        #     No Symptoms to record
                        pass

            messages.success(request, "Contact CT%s:%s %s added to Case C%s." % (this_contact.contact_id,
                                                                                 this_person.first,
                                                                                 this_person.last,
                                                                                 case.case_id))

            if 'save_and_exit' in request.POST:
                return redirect('info', cttype=cttype, pid=pid)
            elif 'save_and_add_another' in request.POST:
                return redirect('/TracingApp/add-contact/%s/%s' % (cttype, pid))
            else:
                return redirect('assignments')

    else:
        personform = PersonForm(instance=person)
        relationform = AddCaseRelation()
        usecasephoneform = AddCasePhoneForContact()

        addressforms = AddressFormSet(queryset=addressquery, prefix='address')
        # phonequery = PersonPhoneJoin.objects.filter(person_id=case.person_id)
        phoneforms = PhoneFormSet(queryset=phone_query, prefix='phone')
        emailforms = EmailFormSet(queryset=email_query, prefix='email')
        contactform = AddContactForm(instance=contact)
        logform = ContactTraceLogForm(user, instance=log)

        symptomlogforms = SymptomLogFormSet(queryset=symptom_query, prefix='sxlog')

    return render(request, 'contacts/add-contact.html', {'contactform': contactform,
                                                         'personform': personform,
                                                         'relationform': relationform,
                                                         'addressforms': addressforms,
                                                         'addressformhelper': addressformhelper,
                                                         'usecasephoneform': usecasephoneform,
                                                         'phoneforms': phoneforms,
                                                         'phoneformhelper': phoneformhelper,
                                                         'emailforms': emailforms,
                                                         'emailformhelper': emailformhelper,
                                                         'symptomlogforms': symptomlogforms,
                                                         'symptomloghelper': symptomloghelper,
                                                         'logform': logform,
                                                         })


@login_required(login_url='/accounts/login/')
def followup(request, cttype, pid):

    pending = AssignmentStatus.objects.get(status_id=1)

    if cttype == 'C':
        case = get_object_or_404(Cases, case_id=pid)
        symptom_query = CaseSxJoin.objects.filter(case_id=case)
        trace_log_query = CaseLogJoin.objects.filter(case_id=case)
        test = case.test_id
        test_query = CaseTestJoin.objects.filter(case_id=case)
        user = AuthUser.objects.get(id=request.user.id)
        this_assignment, a_created = Assignments.objects.get_or_create(case=case, user=user, status=pending)
    elif cttype == 'CT':
        case = get_object_or_404(Contacts, contact_id=pid)
        symptom_query = ContactSxJoin.objects.filter(case_id=case)
        trace_log_query = ContactLogJoin.objects.filter(contact_id=case)
        test = 0
        test_query = ContactTestJoin.objects.filter(contact_id=case)
        user = AuthUser.objects.get(id=request.user.id)
        this_assignment, a_created = Assignments.objects.get_or_create(contact=case, user=user, status=pending)
    else:
        return Http404("Invalid type.")

    person = Persons.objects.get(person_id=case.person_id)
    test_query = Tests.objects.filter(test_id__in=test_query.values('test_id'))
    if len(test_query) > 0:
        test_extra = 0
    else:
        test_extra = 1

    # print(symptom_query)

    address_query = PersonAddressJoin.objects.filter(person=person).values('address')
    # print(address_query)
    phone_query = PersonPhoneJoin.objects.filter(person=person).values('phone')
    email_query = PersonEmailJoin.objects.filter(person=person).values('email')

    if len(address_query) > 0:
        address_extra = 0
    else:
        address_extra = 1

    if len(phone_query) > 0:
        phone_extra = 0
    else:
        phone_extra = 1

    if len(email_query) > 0:
        email_extra = 0
    else:
        email_extra = 1

    AddressFormSet = modelformset_factory(Addresses, form=AddressesForm, extra=address_extra)
    PhoneFormSet = modelformset_factory(Phones, form=PhoneForm, extra=phone_extra)
    EmailFormSet = modelformset_factory(Emails, form=EmailForm, extra=email_extra)
    SymptomFormSet = modelformset_factory(SxLog, form=OldSymptomLogForm, extra=0)
    TraceLogFormSet = modelformset_factory(TraceLogs, form=TraceLogForm, extra=0)
    TestFormSet = modelformset_factory(Tests, form=NewTest, extra=test_extra)

    new_log = TraceLogs()
    NewSymptomFormSet = modelformset_factory(SxLog, form=NewSymptomLogForm, extra=1)
    # NewTraceLogFormSet = modelformset_factory(TraceLogs, form=NewTraceLogForm, extra=1)

    addressformhelper = AddressesFormHelper()
    phoneformhelper = PhoneFormHelper()
    emailformhelper = EmailFormHelper()
    symptomloghelper = SymptomLogSetHelper()
    traceloghelper = OldTraceLogFormHelper()
    testformhelper = NewTestFormHelper()

    if request.method == 'POST':
        if cttype == 'C':
            caseform = FollowUpCaseForm(request.POST, instance=case)
        elif cttype == 'CT':
            caseform = FollowUpContactForm(request.POST, instance=case)
        else:
            return Http404("Invalid type.")

        personform = PersonForm(request.POST, instance=person)
        # print(address_query)
        addressforms = AddressFormSet(request.POST, queryset=Addresses.objects.filter(address_id__in=address_query), prefix='address')
        phoneforms = PhoneFormSet(request.POST, queryset=Phones.objects.filter(phone_id__in=phone_query), prefix='phone')
        emailforms = EmailFormSet(request.POST, queryset=Emails.objects.filter(email_id__in=email_query), prefix='email')
        symptomforms = SymptomFormSet(request.POST, queryset=SxLog.objects.filter(log_id__in=symptom_query.values('sx_id')).order_by('symptom'))
        tracelogforms = TraceLogFormSet(request.POST, queryset=TraceLogs.objects.filter(log_id__in=trace_log_query.values('log')))
        new_tracelogform = ContactTraceLogForm(user, request.POST, instance=new_log)
        new_symptomforms = NewSymptomFormSet(request.POST, prefix='sxlog',
                                             queryset=SxLog.objects.none())
        newtestforms = TestFormSet(request.POST, queryset=test_query, prefix='new_test')

        # print(test)
        # print(len(test))

        if test is not None:
            if test > 0:
                try:
                    testforms = Tests.objects.filter(test_id=test)
                except ValueError:
                    testforms = None
            else:
                testforms = None
        else:
            testforms = None

        print("Case: %s" % caseform.is_valid())
        print("Person: %s" % personform.is_valid())
        print("Email: %s" % emailforms.is_valid())
        print("Address: %s" % addressforms.is_valid())
        print("Phone: %s" % phoneforms.is_valid())
        print("Log: %s" % new_tracelogform.is_valid())
        print("Symptom: %s" % new_symptomforms.is_valid())

        print(addressforms.errors)

        if caseform.is_valid() \
                and personform.is_valid() \
                and emailforms.is_valid() \
                and addressforms.is_valid() \
                and newtestforms.is_valid() \
                and phoneforms.is_valid() \
                and new_tracelogform.is_valid() \
                and new_symptomforms.is_valid():

            if personform.has_changed():
                this_person = personform.save()
            else:
                this_person = person

            for addressform in addressforms:
                if addressform.is_valid():
                    this_address = addressform.save()
                    person_address, created = PersonAddressJoin.objects.update_or_create(person=this_person, address=this_address)
                    if created:
                        person_address.save()

            for phoneform in phoneforms:
                if phoneform.is_valid():
                    this_phone = phoneform.save()
                    person_phone, created = PersonPhoneJoin.objects.update_or_create(person=this_person, phone=this_phone)
                    if created:
                        person_phone.save()

            for emailform in emailforms:
                if emailform.is_valid():
                    this_email = emailform.save()
                    person_email, created = PersonEmailJoin.objects.update_or_create(person=this_person, email=this_email)
                    if created:
                        person_email.save()

            if new_tracelogform.cleaned_data['notes']:
                this_log = new_tracelogform.save()
                if cttype == 'C':
                    case_log = CaseLogJoin(case=case, log=this_log)
                    case_log.save()
                elif cttype == 'CT':
                    contact_log = ContactLogJoin(contact=case, log=this_log)
                    contact_log.save()

            for newtestform in newtestforms:
                if newtestform.is_valid():
                    this_test = newtestform.save(commit=False)
                    this_test.user = user
                    this_test.logged_date = datetime.date.today()
                    this_test.save()
                    if cttype == 'C':
                        test_link = CaseTestJoin(case=case, test=this_test)
                        test_link.save()
                    elif cttype == 'CT':
                        test_link = ContactTestJoin(contact=case, test=this_test)
                        test_link.save()

            for new_symptomform in new_symptomforms:
                if new_symptomform.is_valid():
                    try:
                        if new_symptomform.cleaned_data['symptom']:
                            this_symptom = new_symptomform.save(commit=False)
                            this_symptom.user = user
                            this_symptom.save()
                            if cttype == 'C':
                                case_sx = CaseSxJoin(case=case, sx=this_symptom)
                                case_sx.save()
                            elif cttype == 'CT':
                                contact_sx = ContactSxJoin(case=case, sx=this_symptom)
                                contact_sx.save()
                    except KeyError:
                        #     No Symptoms to record
                        pass

            print("Caseform chanaged?")
            print(caseform.changed_data)

            print("last_follow initial: %s | last_follow current: %s" % (caseform['last_follow'].initial, caseform.cleaned_data['last_follow']))
            print("active initial: %s | active current: %s" % (
            caseform['active'].initial, caseform.cleaned_data['active']))

            this_caseform = caseform.save(commit=False)

            if caseform.has_changed():
                # print("It's changed")
                if cttype == 'CT':
                    # print("It's a contact")
                    # print(caseform.cleaned_data['status'])
                    if caseform.cleaned_data['status'] == Statuses.objects.get(status_id=9) or \
                            caseform.cleaned_data['status'] == Statuses.objects.get(status_id=10):
                        # print("Caseform changed and marked as case")
                        this_caseform.active = False
                        print("Just set to inactive, is it?")
                        print(this_caseform.active)

                        # print(caseform.cleaned_data['active'])
                        this_status = caseform.cleaned_data['status']
                        today = datetime.date.today()

                        upgraded_case = Cases(person=this_person,
                                              status=this_status,
                                              last_follow=today,
                                              active=1,
                                              )

                        if caseform.cleaned_data['status'] == Statuses.objects.get(status_id=9):
                            upgraded_case.probable = True

                        upgraded_case.save()

                        all_symptoms = ContactSxJoin.objects.filter(case_id=pid).values('sx_id')
                        for symptom in all_symptoms:
                            # current_symptom = SxLog.objects.get(log_id=symptom)
                            case_sx = CaseSxJoin(case=upgraded_case, sx_id=symptom['sx_id'])
                            case_sx.save()

                        note_data = {'contact': pid,
                                     'date': today,
                                     'case': upgraded_case.case_id,
                                     'status': this_status,
                                     }
                        note = 'Contact CT{contact} has been {status}. New ID is C{case}.'.format(**note_data)
                        upgrade_log = TraceLogs(notes=note, user=user, log_date=today)
                        this_new_log = upgrade_log.save()
                        contact_log2 = ContactLogJoin(contact=case, log=upgrade_log)
                        contact_log2.save()

                        all_logs = ContactLogJoin.objects.filter(contact_id=pid).values('log_id')
                        for log in all_logs:
                            new_case_log = CaseLogJoin(case=upgraded_case, log_id=log['log_id'])
                            new_case_log.save()

                        linked_cases = CaseContactJoin.objects.filter(contact=case)
                        # print(linked_cases)

                        for linked_case in linked_cases:
                            # print(linked_case.case)
                            this_link = CaseLinks(exposing_case=linked_case.case,
                                                  developed_case=upgraded_case,
                                                  developed_contact=this_caseform)
                            this_link.save()

                if caseform.cleaned_data['status'] == Statuses.objects.get(status_id=5) or \
                        caseform.cleaned_data['status'] == Statuses.objects.get(status_id=11) or\
                        caseform.cleaned_data['status'] == Statuses.objects.get(status_id=12) or\
                        caseform.cleaned_data['status'] == Statuses.objects.get(status_id=13) or\
                        caseform.cleaned_data['status'] == Statuses.objects.get(status_id=14):

                    print("Secondary, by status:")
                    print(caseform.cleaned_data['status'])
                    this_caseform.active = False

                        # print("Case upgraded")

            print('Active: %s' % caseform.cleaned_data['active'])
            this_caseform.last_follow = datetime.date.today()
            # caseform.cleaned_data['last_follow'] = datetime.date.today()
            print("Before caseform is saved, inactive?")
            print(this_caseform.active)
            this_caseform.save()

            done_status = AssignmentStatus.objects.get(status_id=2)

            if a_created:
                this_assignment.assign_type = 4
            this_assignment.status = done_status
            this_assignment.date_done = datetime.date.today()
            this_assignment.save()

            if 'save_and_exit' in request.POST:
                # print('save_exit')
                return redirect('info', cttype=cttype, pid=pid)
            elif 'save_and_add_contacts' in request.POST:
                # print('save_contacts')
                return redirect('/TracingApp/add-contact/%s/%s' % (cttype, pid))
            else:
                return redirect('assignments')



    else:
        if cttype == 'C':
            caseform = FollowUpCaseForm(instance=case)
        elif cttype == 'CT':
            caseform = FollowUpContactForm(instance=case)
        else:
            return Http404("Invalid type.")

        personform = PersonForm(instance=person)
        addressforms = AddressFormSet(queryset=Addresses.objects.filter(address_id__in=address_query), prefix='address')
        phoneforms = PhoneFormSet(queryset=Phones.objects.filter(phone_id__in=phone_query), prefix='phone')
        emailforms = EmailFormSet(queryset=Emails.objects.filter(email_id__in=email_query), prefix='email')
        symptomforms = SymptomFormSet(queryset=SxLog.objects.filter(log_id__in=symptom_query.values('sx_id')).order_by('symptom'))
        print(symptom_query)
        print("FORMS:")
        print(symptomforms)
        tracelogforms = TraceLogFormSet(queryset=TraceLogs.objects.filter(log_id__in=trace_log_query.values('log')))
        new_tracelogform = ContactTraceLogForm(user, request.POST, instance=new_log)
        new_symptomforms = NewSymptomFormSet(prefix='sxlog',
                                             queryset=SxLog.objects.none())
        newtestforms = TestFormSet(prefix='new_test', queryset=test_query)

        print(test_query)
        # A contact shouldn't have a test
        testforms = Tests.objects.none()

    return render(request, 'follow-up.html', {'caseform': caseform,
                                              'personform': personform,
                                              'addressforms': addressforms,
                                              'addressformhelper': addressformhelper,
                                              'phoneforms': phoneforms,
                                              'phoneformhelper': phoneformhelper,
                                              'emailforms': emailforms,
                                              'emailformhelper': emailformhelper,
                                              'symptomforms': symptomforms,
                                              'symptomloghelper': symptomloghelper,
                                              'tracelogforms': tracelogforms,
                                              'tracelogformhelper': traceloghelper,
                                              'new_tracelogform': new_tracelogform,
                                              'new_symptomforms': new_symptomforms,
                                              'testforms': testforms,
                                              'type': cttype,
                                              'newtestforms': newtestforms,
                                              'testformhelper': testformhelper,
                                              })


@login_required(login_url='/accounts/login/')
def assign_contacts_cases(request):

    cases = Cases.objects.filter(active=1).order_by('last_follow', 'case_id')
    CaseAssignmentFormsest = formset_factory(AssignCaseForm, extra=len(cases))

    contacts = Contacts.objects.filter(active=1).order_by('last_follow', 'contact_id')
    ContactAssignmentFormset = formset_factory(AssignCaseForm, extra=len(contacts))

    assignment = Assignments()

    users = AuthUser.objects.filter(id__gt=0)

    pending_status = AssignmentStatus.objects.get(status_id=1)

    if request.method == 'POST':
        # print('POST')

        caseassignments = CaseAssignmentFormsest(request.POST, prefix='case')
        contactassignments = ContactAssignmentFormset(request.POST, prefix='contact')

        assignform = NewAssignment(request.POST, instance=assignment)

        # for x in caseassignments:
        #     x.fields['case_id'].value = Cases.objects.get(case_id=1)
        #     x.fields['status'].initial = Statuses.objects.get(status_id=1)
        #     x.fields['person'].initial = Persons.objects.get(person_id=1)
        #     x.fields['test'].initial = Tests.objects.get(test_id=1)

        # print(caseassignments.is_valid())
        # print(assignform.is_valid())

        if caseassignments.is_valid() and assignform.is_valid() and contactassignments.is_valid():
            i = 0
            j = 0
            for caseassign in caseassignments:
                # print('in for')
                if caseassign.is_valid():
                    # print('valid form')
                    print(caseassign.cleaned_data)
                    if caseassign.cleaned_data['assign_box']:
                        # print('checked box')
                        this_assign = Assignments(user=assignform.cleaned_data['user'],
                                                  case=cases[i],
                                                  status=pending_status,
                                                  assign_type=assignform.cleaned_data['assign_type'])
                        this_assign.save()
                i = i + 1

            for contactassign in contactassignments:
                if contactassign.is_valid():
                    # print('valid form')
                    # print(contactassign.cleaned_data)
                    if contactassign.cleaned_data['assign_box']:
                        # print('checked box')
                        this_assign = Assignments(user=assignform.cleaned_data['user'],
                                                  contact=contacts[j],
                                                  status=pending_status,
                                                  assign_type=assignform.cleaned_data['assign_type'])
                        this_assign.save()
                j = j + 1

            return redirect('assignments')
        print(caseassignments.errors)

    else:

        caseassignments = CaseAssignmentFormsest(prefix='case')
        contactassignments = ContactAssignmentFormset(prefix='contact')

        assignform = NewAssignment(instance=assignment, initial={'status': 1})
        # caseassignments = AssignCaseForm()

        # print(caseassignments)

    return render(request, 'bulk-assign/multiple-assign.html', {'assigncases': zip(caseassignments, cases),
                                                                'assignform': assignform,
                                                                'assignformset': caseassignments,
                                                                'assigncontacts': zip(contactassignments, contacts),
                                                                'contactformset': contactassignments,
                                                                # 'cases': cases[0],
                                                                })


@login_required(login_url='/accounts/login/')
def create_household(request):

    if request.method == 'POST':

        householdform = HouseHoldForm(request.POST)

        # print("HH form valid?")
        # print(householdform.is_valid())
        if householdform.is_valid():
            persons = householdform.cleaned_data['people']

            this_household = HouseHolds()
            this_household.save()

            for person in persons:
                # print(person.person_id)
                this_hh_person = HHPersonJoin(household=this_household, person=person)
                this_hh_person.save()

            if 'save_and_exit' in request.POST:
                # print('save_exit')
                return redirect('household')
            elif 'save_and_add_contacts' in request.POST:
                # print('save_contacts')
                return redirect('/TracingApp/household/new')
            else:
                return redirect('assignments')

    else:
        householdform = HouseHoldForm()

    return render(request, 'household/create-household.html', {'householdform': householdform,
                                                               })


@login_required(login_url='/accounts/login/')
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        print(form.is_valid())
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('change_password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {
        'form': form
    })


@login_required(login_url='/accounts/login/')
def search_results(request):
    query = request.GET.get('q')

    persons = Persons.objects.filter(Q(last__icontains=query) | Q(first__icontains=query))
    cases_p = None
    contacts_p = None
    cases = None
    contacts = None

    print(persons)

    if persons:
        cases_p = Cases.objects.filter(person_id__in=persons)
        contacts_p = Contacts.objects.filter(person_id__in=persons)

    # print(cases_p)

    is_case = re.search('C\d+', query)
    is_contact = re.search('CT\d+', query)

    print(is_case)

    if is_case is not None:
        case_query = re.findall('\d+', query)
        cases = Cases.objects.filter(Q(case_id=case_query[0]) | Q(old_case_no="C%s" % case_query[0]))
    elif is_contact is not None:
        contact_query = re.findall('\d+', query)
        # print(contact_query)
        contacts = Contacts.objects.filter(
            Q(contact_id=contact_query[0]) | Q(old_contact_no="CT%s" % contact_query[0]))
    elif len(persons) == 0:
        print("should be the case")
        case_query = re.findall('\d+', query)
        cases = Cases.objects.filter(Q(case_id=case_query[0]) | Q(old_case_no="C%s" % case_query[0]))
        contacts = Contacts.objects.filter(
            Q(contact_id=case_query[0]) | Q(old_contact_no="CT%s" % case_query[0]))

    return render(request, 'search.html', {'cases_p': cases_p,
                                           'contacts_p': contacts_p,
                                           'cases': cases,
                                           'contacts': contacts,
                                           })
