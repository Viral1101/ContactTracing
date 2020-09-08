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
        testforms = Tests.objects.filter(test_id=data.test_id)
        upstream_cases = CaseLinks.objects.filter(developed_case=data)
        downstream_cases = CaseLinks.objects.filter(exposing_case=data)
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
        testforms = Tests.objects.none()
        upstream_cases = None
        downstream_cases = None
    else:
        raise Http404("Invalid case type")

    if data is None:
        raise Http404("No data for this case exists")

    if sxs:
        # print(sxs)
        sx_ids = sxs.values('sx_id')
        # symptoms = SxLogJoin.objects.filter(sx_id__in=sx_ids)
        # sx_logs = SxLog.objects.filter(log_id__in=symptoms)
        symptoms = SxLog.objects.filter(log_id__in=sx_ids)
        sx_logs = symptoms
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
    # test.logged_date = datetime.date.today()
    # print(test.logged_date)

    if request.method == "POST":

        # print("POST")
        personform = NewPersonForm(request.POST, instance=person)
        addressform = NewAddressForm(request.POST, instance=address)
        phoneform = NewPhoneNumberForm(request.POST, instance=phone)
        assignform = NewAssignment(request.POST, instance=assignment, initial={'status': False, 'assign_type': 1})

        # today = datetime.date.today()
        testform = NewTest(request.user, request.POST, instance=test)
        # testform.logged_date = datetime.date.today()

        # assignform_valid = assignform.is_valid()
        # testform_valid = testform.is_valid()
        # personform_valid = personform.is_valid()
        # addressform_valid = addressform.is_valid()
        # phoneform_valid = phoneform.is_valid()

        # print('Assign: %s || Test: %s || Person: %s || Address: %s || Phone: %s' %
        #       (assignform_valid, testform_valid, personform_valid, addressform_valid, phoneform_valid))
        # print(testform.cleaned_data['logged_date'])

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
            new_test = testform.save()
            # print("saved test")
            new_person = personform.save()
            # print("saved person")

            personaddress = PersonAddressJoin(person=new_person, address=new_address)
            personphone = PersonPhoneJoin(person=new_person, phone=new_phone)

            personaddress.save()
            personphone.save()
            # print("saved personphone")

            needs_invest_status = Statuses.objects.get(status_id=1)
            newcase = Cases(person=new_person, test=new_test, active=True, status=needs_invest_status)
            # print("made newcase")

            newassign = Assignments(case=newcase,
                                    assign_type=assignform.cleaned_data['assign_type'],
                                    status=assignform.cleaned_data['status'],
                                    user=assignform.cleaned_data['user'])
            # print("made newassign")

            new_person.save()
            new_test.save()
            newcase.save()
            newassign.save()
            assignform.save()

            return redirect('assignments')

    else:
        personform = NewPersonForm(instance=person)
        addressform = NewAddressForm(instance=address, initial={'state':'MO'})
        phoneform = NewPhoneNumberForm(instance=phone)
        assignform = NewAssignment(instance=assignment, initial={'status': False, 'assign_type': 1})
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
    user = AuthUser.objects.get(id=request.user.id)
    # addressesJoins = PersonAddressJoin.objects.filter(person=person)
    # addresses = Addresses.objects.filter(address_id__in=addressesJoi
    # ns.values('address_id'))

    AddressFormSet = modelformset_factory(Addresses,  form=AddressesForm, extra=0)
    PhoneFormSet = modelformset_factory(Phones, form=PhoneForm, extra=0)

    NewTestFormSet = modelformset_factory(Tests, form=NewTest, extra=0) #for adding new tests if needed
    EmailFormSet = modelformset_factory(Emails, form=EmailForm, extra=1)

    SymptomFormSet = modelformset_factory(Symptoms, form=SymptomForm, extra=1)
    SymptomLogFormSet = modelformset_factory(SxLog, form=NewSymptomLogForm, extra=1)
    symptomloghelper = SymptomLogSetHelper()

    addressformhelper = AddressesFormHelper()
    emailformhelper = EmailFormHelper()
    phoneformhelper = PhoneFormHelper()
    testformhelper = TestFormHelper()

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
        testform = GetTest(request.POST, instance=test)
        logform = NewTraceLogForm(user, request.POST, instance=log)

        addressforms = AddressFormSet(request.POST, prefix='address', queryset=addressquery)
        emailforms = EmailFormSet(request.POST, prefix='email', queryset=emailquery)
        new_testforms = NewTestFormSet(user, request.POST, prefix='new_test')

        # phone_query = PersonPhoneJoin.objects.filter(person_id=case.person_id)
        phoneforms = PhoneFormSet(request.POST, prefix='phone', queryset=phone_query)
        symptomforms = SymptomFormSet(request.POST, prefix='symptom')
        symptomlogforms = SymptomLogFormSet(request.POST, prefix='sxlog', form_kwargs={'user': user},
                                            queryset=symptom_query)

        for symptomlogform in symptomlogforms:
            symptomlogform.user = user

        logform.user = user
            # symptomlogform.rec_date = datetime.date.today()

        # print("Case: %s | Person: %s | Address: %s | Phone: %s | Email: %s | Test: %s | Log: %s | Sx: %s" %
        #       (caseform.is_valid(),
        #        personform.is_valid(),
        #        addressforms.is_valid(),
        #        emailforms.is_valid(),
        #        phoneforms.is_valid(),
        #        testform.is_valid(),
        #        logform.is_valid(),
        #        symptomlogforms.is_valid()))

        if caseform.is_valid() \
                and personform.is_valid()\
                and testform.is_valid()\
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

            for phoneform in phoneforms:
                if phoneform.is_valid():
                    this_phone = phoneform.save()
                    person_phone, created2 = PersonPhoneJoin.objects.get_or_create(person=this_person, phone=this_phone)
                    person_phone.save()
                    # this_phone.save()

            for emailform in emailforms:
                if emailform.is_valid():
                    this_email = emailform.save()
                    person_email, created4 = PersonEmailJoin.objects.get_or_create(person=this_person, email=this_email)
                    person_email.save()

            this_test = testform.save(commit=False)

            caseform.cleaned_data['test'] = this_test
            caseform.cleaned_data['person'] = this_person

            this_case = caseform.save(commit=False)
            this_log = logform.save()

            # print(this_log)

            case_log, log_created = CaseLogJoin.objects.get_or_create(case=this_case, log=this_log)
            case_log.save()

            for symptomlogform in symptomlogforms:
                if symptomlogform.is_valid():
                    try:
                        if symptomlogform.cleaned_data['symptom']:
                            this_symptom = symptomlogform.save()
                            case_sx, created3 = CaseSxJoin.objects.get_or_create(case=this_case, sx=this_symptom)
                            case_sx.save()
                    except KeyError:
                        #     No Symptoms to record
                        pass

            this_test.save()
            this_person.save()
            this_case.save()

            # Mark the assignment as done with the date
            this_assignment = Assignments.objects.get(case=this_case, user=user)
            this_assignment.status = 1
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
        testform = GetTest(instance=test)
        new_testforms = NewTestFormSet(user, queryset=Tests.objects.none(), prefix='new_test')

        addressforms = AddressFormSet(queryset=addressquery, prefix='address')
        emailforms = EmailFormSet(prefix='email', queryset=emailquery)
        # phonequery = PersonPhoneJoin.objects.filter(person_id=case.person_id)
        phoneforms = PhoneFormSet(queryset=phone_query, prefix='phone')
        caseform = InvestigationCaseForm(instance=case)
        logform = NewTraceLogForm(user, instance=log)

        symptomforms = SymptomFormSet(queryset=Symptoms.objects.none())
        symptomlogforms = SymptomLogFormSet(queryset=symptom_query, form_kwargs={'user': user}, prefix='sxlog')

    return render(request, 'case edit/case-investigation.html', {'caseform': caseform,
                                                                 'personform': personform,
                                                                 'addressforms': addressforms,
                                                                 'addressformhelper': addressformhelper,
                                                                 'emailforms': emailforms,
                                                                 'emailformhelper': emailformhelper,
                                                                 'phoneforms': phoneforms,
                                                                 'phoneformhelper': phoneformhelper,
                                                                 'testform': testform,
                                                                 'testformhelper': testformhelper,
                                                                 'new_testforms': new_testforms,
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

    if request.method == 'POST':

        contactform = AddContactForm(request.POST, instance=contact)
        personform = PersonForm(request.POST, instance=person)
        logform = ContactTraceLogForm(request.user, request.POST, instance=log)

        addressforms = AddressFormSet(request.POST, prefix='address')
        phoneforms = PhoneFormSet(request.POST, prefix='phone')
        emailforms = EmailFormSet(request.POST, prefix='email')

        symptomlogforms = SymptomLogFormSet(request.POST, form_kwargs={'user': request.user}, prefix='sxlog')

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

        logform.user = request.user.id

        # for thing in addressforms:
            # print(thing.errors)

        if contactform.is_valid() \
                and personform.is_valid() \
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
                this_log = logform.save()
                contact_log, ctd2 = ContactLogJoin.objects.get_or_create(contact=this_contact, log=this_log)

            contact_log.save()

            case_contact, ctd = CaseContactJoin.objects.get_or_create(case=case, contact=this_contact)
            case_contact.save()

            for addressform in addressforms:
                if addressform.cleaned_data['use_case_address']:
                    case_address = PersonAddressJoin.objects.filter(person=case.person).first().address
                    person_address, created = PersonAddressJoin.objects.get_or_create(person=this_person,
                                                                                      address=case_address)
                    person_address.save()
                elif addressform.is_valid():
                    try:
                        if addressform.cleaned_data['street']:
                            this_address = addressform.save()
                            person_address, created = PersonAddressJoin.objects.get_or_create(person=this_person,
                                                                                              address=this_address)
                            person_address.save()
                            # this_address.save()
                    except KeyError:
                        #     No Symptoms to record
                        pass

            for phoneform in phoneforms:
                if phoneform.cleaned_data['use_case_phone']:
                    case_phone = PersonPhoneJoin.objects.filter(person=case.person).first().phone
                    person_phone, created2 = PersonPhoneJoin.objects.get_or_create(person=this_person, phone=case_phone)
                    person_phone.save()
                elif phoneform.is_valid():
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
                            this_symptom = symptomlogform.save()
                            case_sx, created3 = ContactSxJoin.objects.get_or_create(case=this_contact, sx=this_symptom)
                            case_sx.save()
                    except KeyError:
                        #     No Symptoms to record
                        pass

            if 'save_and_exit' in request.POST:
                return redirect('info', cttype=cttype, pid=pid)
            elif 'save_and_add_another' in request.POST:
                return redirect('/TracingApp/add-contact/%s/%s' % (cttype, pid))
            else:
                return redirect('assignments')

    else:
        personform = PersonForm(instance=person)

        addressforms = AddressFormSet(queryset=addressquery, prefix='address')
        # phonequery = PersonPhoneJoin.objects.filter(person_id=case.person_id)
        phoneforms = PhoneFormSet(queryset=phone_query, prefix='phone')
        emailforms = EmailFormSet(queryset=email_query, prefix='email')
        contactform = AddContactForm(instance=contact)
        logform = ContactTraceLogForm(request.user, instance=log)

        symptomlogforms = SymptomLogFormSet(queryset=symptom_query, form_kwargs={'user': request.user}, prefix='sxlog')

    return render(request, 'contacts/add-contact.html', {'contactform': contactform,
                                                         'personform': personform,
                                                         'addressforms': addressforms,
                                                         'addressformhelper': addressformhelper,
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

    if cttype == 'C':
        case = get_object_or_404(Cases, case_id=pid)
        symptom_query = CaseSxJoin.objects.filter(case_id=case)
        trace_log_query = CaseLogJoin.objects.filter(case_id=case)
        test = case.test_id
        user = AuthUser.objects.get(id=request.user.id)
        this_assignment, a_created = Assignments.objects.get_or_create(case=case, user=user, status=0)
    elif cttype == 'CT':
        case = get_object_or_404(Contacts, contact_id=pid)
        symptom_query = ContactSxJoin.objects.filter(case_id=case)
        trace_log_query = ContactLogJoin.objects.filter(contact_id=case)
        test = Tests.objects.none()
        user = AuthUser.objects.get(id=request.user.id)
        this_assignment, a_created = Assignments.objects.get_or_create(contact=case, user=user, status=0)
    else:
        return Http404("Invalid type.")

    person = Persons.objects.get(person_id=case.person_id)

    # print(symptom_query)

    AddressFormSet = modelformset_factory(Addresses, form=AddressesForm, extra=0)
    PhoneFormSet = modelformset_factory(Phones, form=PhoneForm, extra=0)
    EmailFormSet = modelformset_factory(Emails, form=EmailForm, extra=0)
    SymptomFormSet = modelformset_factory(SxLog, form=OldSymptomLogForm, extra=0)
    TraceLogFormSet = modelformset_factory(TraceLogs, form=TraceLogForm, extra=0)

    new_log = TraceLogs()
    NewSymptomFormSet = modelformset_factory(SxLog, form=NewSymptomLogForm, extra=1)
    # NewTraceLogFormSet = modelformset_factory(TraceLogs, form=NewTraceLogForm, extra=1)

    addressformhelper = AddressesFormHelper()
    phoneformhelper = PhoneFormHelper()
    emailformhelper = EmailFormHelper()
    symptomloghelper = SymptomLogSetHelper()
    traceloghelper = OldTraceLogFormHelper()

    address_query = PersonAddressJoin.objects.filter(person=person).values('address')
    # print(address_query)
    phone_query = PersonPhoneJoin.objects.filter(person=person).values('phone')
    email_query = PersonEmailJoin.objects.filter(person=person).values('email')

    if request.method == 'POST':
        if cttype == 'C':
            caseform = CaseForm(request.POST, instance=case)
        elif cttype == 'CT':
            caseform = FollowUpContactForm(request.POST, instance=case)
        else:
            return Http404("Invalid type.")

        personform = PersonForm(request.POST, instance=person)
        addressforms = AddressFormSet(request.POST, queryset=Addresses.objects.filter(address_id__in=address_query))
        phoneforms = PhoneFormSet(request.POST, queryset=Phones.objects.filter(phone_id__in=phone_query))
        emailforms = EmailFormSet(request.POST, queryset=Emails.objects.filter(email_id__in=email_query))
        symptomforms = SymptomFormSet(request.POST, queryset=SxLog.objects.filter(log_id__in=symptom_query).order_by('symptom').order_by('-rec_date'))
        tracelogforms = TraceLogFormSet(request.POST, queryset=TraceLogs.objects.filter(log_id__in=trace_log_query.values('log')))
        new_tracelogform = ContactTraceLogForm(user, request.POST, instance=new_log)
        new_symptomforms = NewSymptomFormSet(request.POST, prefix='sxlog', form_kwargs={'user': user},
                                             queryset=SxLog.objects.none())

        try:
            testforms = Tests.objects.filter(test_id=test)
        except ValueError:
            testforms = None

        if caseform.is_valid() \
                and personform.is_valid() \
                and emailforms.is_valid() \
                and addressforms.is_valid() \
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

            for new_symptomform in new_symptomforms:
                if new_symptomform.is_valid():
                    try:
                        if new_symptomform.cleaned_data['symptom']:
                            this_symptom = new_symptomform.save()
                            if cttype == 'C':
                                case_sx = CaseSxJoin(case=case, sx=this_symptom)
                                case_sx.save()
                            elif cttype == 'CT':
                                contact_sx = ContactSxJoin(case=case, sx=this_symptom)
                                contact_sx.save()
                    except KeyError:
                        #     No Symptoms to record
                        pass

            # print("Caseform chanaged?")
            # print(caseform.changed_data)

            if caseform.has_changed():
                # print("It's changed")
                if cttype == 'CT':
                    # print("It's a contact")
                    # print(caseform.cleaned_data['status'])
                    if caseform.cleaned_data['status'] == Statuses.objects.get(status_id=9) or \
                            caseform.cleaned_data['status'] == Statuses.objects.get(status_id=10):
                        # print("Caseform changed and marked as case")
                        caseform.cleaned_data['active'] = False

                        # print(caseform.cleaned_data['active'])
                        this_status = caseform.cleaned_data['status']
                        today = datetime.date.today()

                        upgraded_case = Cases(person=this_person,
                                              status=this_status,
                                              last_follow=today,
                                              active=1,
                                              )
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
                            this_link = CaseLinks(exposing_case=linked_case.case, developed_case=upgraded_case)
                            this_link.save()

                elif caseform.cleaned_data['status'] == Statuses.objects.get(status_id=5) or \
                        caseform.cleaned_data['status'] == Statuses.objects.get(status_id=11) or\
                        caseform.cleaned_data['status'] == Statuses.objects.get(status_id=12) or\
                        caseform.cleaned_data['status'] == Statuses.objects.get(status_id=13):

                    caseform.cleaned_data['active'] = False
                else:
                    caseform.cleaned_data['active'] = True

                        # print("Case upgraded")

            print('Active: %s' % caseform.cleaned_data['active'])
            caseform.cleaned_data['last_follow'] = datetime.date.today()
            caseform.save()

            if a_created:
                this_assignment.assign_type = 4
            this_assignment.status = 1
            this_assignment.date_done = datetime.date.today()
            this_assignment.save()

            return redirect('info', cttype=cttype, pid=pid)

    else:
        if cttype == 'C':
            caseform = CaseForm(instance=case)
        elif cttype == 'CT':
            caseform = FollowUpContactForm(instance=case)
        else:
            return Http404("Invalid type.")

        personform = PersonForm(instance=person)
        addressforms = AddressFormSet(queryset=Addresses.objects.filter(address_id__in=address_query))
        phoneforms = PhoneFormSet(queryset=Phones.objects.filter(phone_id__in=phone_query))
        emailforms = EmailFormSet(queryset=Emails.objects.filter(email_id__in=email_query))
        symptomforms = SymptomFormSet(queryset=SxLog.objects.filter(
            log_id__in=symptom_query))
        tracelogforms = TraceLogFormSet(queryset=TraceLogs.objects.filter(log_id__in=trace_log_query.values('log')))
        new_tracelogform = ContactTraceLogForm(user, request.POST, instance=new_log)
        new_symptomforms = NewSymptomFormSet(prefix='sxlog', form_kwargs={'user': user},
                                             queryset=SxLog.objects.none())

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
                                              })


@login_required(login_url='/accounts/login/')
def assign_contacts_cases(request):

    CaseAssignmentFormsest = modelformset_factory(Cases, form=AssignCaseForm, extra=0)
    cases = Cases.objects.filter(active=1)

    assignment = Assignments()

    users = AuthUser.objects.filter(id__gt=0)

    if request.method == 'POST':
        # print('POST')
        caseassignments = CaseAssignmentFormsest(request.POST, queryset=cases)
        assignform = NewAssignment(request.POST, instance=assignment, initial={'status': False})

        for x in caseassignments:
            x.fields['case_id'].initial = Cases.objects.get(case_id=1)
            x.fields['status'].initial = Statuses.objects.get(status_id=1)
            x.fields['person'].initial = Persons.objects.get(person_id=1)
            x.fields['test'].initial = Tests.objects.get(test_id=1)

        # print(caseassignments.is_valid())
        # print(assignform.is_valid())

        if caseassignments.is_valid() and assignform.is_valid():
            i = 0
            for caseassign in caseassignments:
                # print('in for')
                if caseassign.is_valid():
                    # print('valid form')
                    if caseassign.cleaned_data['assign_box']:
                        # print('checked box')
                        this_assign = Assignments(user=assignform.cleaned_data['user'],
                                                  case=cases[i],
                                                  status=False,
                                                  assign_type=assignform.cleaned_data['assign_type'])
                        this_assign.save()
                i = i + 1

            return redirect('assignments')
        # print(caseassignments.errors)

    else:

        caseassignments = CaseAssignmentFormsest(queryset=cases)
        assignform = NewAssignment(instance=assignment, initial={'status': False})
        # caseassignments = AssignCaseForm()

        # print(caseassignments)

    return render(request, 'bulk-assign/multiple-assign.html', {'assigncases': zip(caseassignments, cases),
                                                                'assignform': assignform,
                                                                'assignformset': caseassignments,
                                                                # 'cases': cases[0],
                                                                })
