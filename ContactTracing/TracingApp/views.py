from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from django.forms import inlineformset_factory, modelformset_factory, formset_factory
from .forms import *
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Q
from .charts import charts
import csv
import io


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

    # print(assignments)

    return render(request, 'home.html', {'types': types,
                                         'cases': as_cases,
                                         'contacts': as_contacts,
                                         'outbreaks': outbreaks})


@login_required(login_url='/accounts/login/')
def cases(request):
    cs_cases = Cases.objects.all()
    # phones = PersonPhoneJoin.objects.all()
    today = date.today()
    # symptoms = CaseSxJoin.objects.all()
    # cs_sx_logs = SxLogJoin.objects.all()
    # logs = CaseLogJoin.objects.all()
    # cs_contacts = CaseContactJoin.objects.all()
    ct_type = 'C'
    cs_name = 'Cases'
    cs_assigns = Assignments.objects.filter(case__in=cs_cases, status=1)

    # print(len(cs_assigns))

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

    if request.user.groups.filter(name='admin_user').exists():
        edit_allowed = True
    else:
        edit_allowed = False

    pending = AssignmentStatus.objects.get(status_id=1)

    if cttype == "C":
        data = Cases.objects.get(case_id=pid)
        exposed = Exposures.objects.filter(exposing_case=data)
        in_contacts = ContactExposureJoin.objects.filter(exposure__in=exposed)
        print(in_contacts)
        sxs = CaseSxJoin.objects.filter(case=data)
        logs = CaseLogJoin.objects.filter(case=data)
        in_name = 'Case'
        last_exposure = None
        contacts_logs = ContactLogJoin.objects.\
            filter(contact__in=in_contacts.values('contact_id'))
        ct_symptoms = ContactSxJoin.objects.filter(case_id__in=in_contacts.values('contact_id'))
        ct_logs = ContactLogJoin.objects.filter(contact_id__in=in_contacts.values('contact_id'))
        testquery = CaseTestJoin.objects.filter(case_id=data)
        upstream_cases = ClusterCaseJoin.objects.filter(case=data).exclude(index_case=data)
        downstream_cases = ClusterCaseJoin.objects.filter(index_case=data).exclude(case=data)
        assigned = Assignments.objects.filter(case_id=pid, status=pending).first()
        cmrs = EpitraxPCHDCaseJoin.objects.filter(case_id=pid)
        exposures = None
        # clusters = ClusterCaseJoin.objects.filter(case_id=pid)
    elif cttype == "CT":
        data = Contacts.objects.filter(contact_id=pid).first()
        # in_contacts = CaseContactJoin.objects.filter(contact=data)
        sxs = ContactSxJoin.objects.filter(case=data)
        logs = ContactLogJoin.objects.filter(contact=data)
        in_name = 'Contact'
        exposures = ContactExposureJoin.objects.filter(contact=data)
        in_contacts = Exposures.objects.filter(exposure_id__in=exposures.values('exposure_id'))
        print(exposures)
        if len(exposures) > 0:
            last_exposure = exposures.first().contact.last_exposure
        else:
            last_exposure = None
        for exposure in exposures:
            if last_exposure is not None and exposure.exposure.last_exposure is not None:
                last_exposure = max(last_exposure, exposure.exposure.last_exposure)
            else:
                last_exposure = exposure.exposure.last_exposure
        # last_exposure = data.last_exposure
        exposed = Exposures.objects.filter(exposure_id__in=exposures.values("exposure_id"))
        contacts_logs = CaseLogJoin.objects.\
            filter(case_id__in=exposed.values('exposing_case_id'))
        print(exposed)
        ct_symptoms = CaseSxJoin.objects.filter(case_id__in=exposed.values('exposing_case_id'))
        ct_logs = CaseLogJoin.objects.filter(case_id__in=exposed.values('exposing_case_id'))
        # print(ct_logs.values('case_id'))
        testquery = ContactTestJoin.objects.filter(contact_id=data)
        upstream_cases = None
        downstream_cases = None
        assigned = Assignments.objects.filter(contact_id=pid, status=pending).first()
        cmrs = EpitraxPCHDCaseJoin.objects.filter(contact_id=pid)
        # clusters = None
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

    trace_log_edits = LogEdits.objects.filter(log_id__in=logs.values('log_id')).order_by('edit_id')

    testforms = Tests.objects.filter(test_id__in=testquery.values('test_id'))

    ct_symptoms_details = SxLogJoin.objects.filter(sx_id__in=ct_symptoms.values('sx_id'))
    # print(symptoms)

    ct_logs_details = TraceLogs.objects.filter(log_id__in=ct_logs.values('log_id'))
    person_id = data.person_id
    # print(person_id)
    phones = PersonPhoneJoin.objects.filter(person_id=person_id)
    # print(phones)
    emails = PersonEmailJoin.objects.filter(person_id=person_id)
    today = date.today()
    qt_release = None
    tent_rel_calc = None

    followup_day = date.today() - timedelta(days=7)

    addresses = PersonAddressJoin.objects.filter(person_id=person_id)

    if symptoms is not None:
        # print("This should be none for this test")
        first_sx = date.today()
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
                existing_assign = Assignments.objects.filter(case_id=pid, status=pending_status).exists()
                this_assign = Assignments(user=user, case_id=pid, status=pending_status)
            elif cttype == 'CT':
                existing_assign = Assignments.objects.filter(contact_id=pid, status=pending_status).exists()
                this_assign = Assignments(user=user, contact_id=pid, status=pending_status)
            else:
                existing_assign = Assignments.objects.filter(outbreak_id=pid, status=pending_status).exists()
                this_assign = Assignments(user=user, outbreak_id=pid, status=pending_status)
            if existing_assign:
                messages.info(request, 'Case has been assigned to another user.')
            else:
                this_assign.save()
            return redirect('info', cttype=cttype, pid=pid)
        elif 'drop_assignment' in request.POST:
            dropped_status = AssignmentStatus.objects.get(status_id=3)
            assigned.status = dropped_status
            assigned.date_done = date.today()
            assigned.save()
            return redirect('assignments')
        else:
            return redirect('assignments')

    # print(assigned)

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
                                                      'exposures': exposures,
                                                      'cmrs': cmrs,
                                                      'tracelogedits': trace_log_edits,
                                                      'edit_allowed': edit_allowed,
                                                      'pid': pid,
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
    # test.logged_date = date.today()
    # print(test.logged_date)

    pending_status = AssignmentStatus.objects.get(status_id=1)

    if request.method == "POST":

        # print("POST")
        personform = NewPersonForm(request.POST, instance=person)
        addressform = NewAddressForm(request.POST, instance=address)
        phoneform = NewPhoneNumberForm(request.POST, instance=phone)
        assignform = NewAssignment(request.POST, instance=assignment, initial={'status': AssignmentStatus.objects.get(status_id=1),
                                                                               'assign_type': 1})

        # today = date.today()
        testform = NewTest(request.POST, instance=test)
        # testform.logged_date = date.today()

        assignform_valid = assignform.is_valid()
        testform_valid = testform.is_valid()
        personform_valid = personform.is_valid()
        addressform_valid = addressform.is_valid()
        phoneform_valid = phoneform.is_valid()

        # print('Assign: %s || Test: %s || Person: %s || Address: %s || Phone: %s' %
        #       (assignform_valid, testform_valid, personform_valid, addressform_valid, phoneform_valid))
        # print(testform.cleaned_data['logged_date'])
        #
        # print(assignform.errors)

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

            # print("saved personphone")

            needs_invest_status = Statuses.objects.get(status_id=1)
            newcase, case_created = Cases.objects.get_or_create(person=new_person, active=True, status=needs_invest_status)
            if case_created:

                personaddress.save()
                personphone.save()

                newcase.save()
                # print("made newcase")

                assigned_user = assignform.cleaned_data['user']
                if assigned_user is not None and assigned_user != AuthUser.objects.get(id=1):

                    newassign = Assignments(case=newcase,
                                            assign_type=assignform.cleaned_data['assign_type'],
                                            status=pending_status,
                                            user=assignform.cleaned_data['user'])
                    # print("made newassign")

                    # new_person.save()
                    # new_test.save()
                    newassign.save()
                # assignform.save()

                if new_test.result_id == 1:
                    if new_test.test_type_id == 1 & new_test.source_id <= 2:
                        newcase.confirmed = True
                        newcase.probable = False
                        newcase.monitor_not_case = False
                        newcase.save()
                    else:
                        newcase.confirmed = False
                        newcase.probable = True
                        newcase.monitor_not_case = False
                        newcase.save()

                case_test = CaseTestJoin(case=newcase, test=test)
                case_test.save()

                messages.success(request, 'Case C%s created for %s %s' % (newcase.case_id, new_person.first, new_person.last))
                return redirect('assignments')
            else:
                messages.error(request,
                               'Case for %s %s failed to be created. Ensure you have entered data appropriately.' % (new_person.first, new_person.last))
                new_test.delete()
                new_person.delete()

                return render(request, 'add-new-case.html', {'personform': personform,
                                                             'addressform': addressform,
                                                             'phoneform': phoneform,
                                                             'assignform': assignform,
                                                             'testform': testform,
                                                             })

    else:
        personform = NewPersonForm(instance=person)
        addressform = NewAddressForm(instance=address, initial={'state': 'MO'})
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

    storage = messages.get_messages(request)
    log_initial = []
    for message in storage:
        log_initial.append("<<Link created>> %s" % message)
    log_initial = str(log_initial).strip('[]').replace("'","")

    case = get_object_or_404(Cases, case_id=pid)
    person = get_object_or_404(Persons, person_id=case.person_id)
    test_1 = CaseTestJoin.objects.filter(case_id=pid)
    test = Tests.objects.filter(test_id__in=test_1.values('test'))
    if len(test) > 0:
        test_extra = 0
    else:
        test_extra = 1
    email = PersonEmailJoin.objects.filter(person=case.person)
    if len(email) > 0:
        email_extra = 0
    else:
        email_extra = 1
    user = AuthUser.objects.get(id=request.user.id)
    log = TraceLogs()
    # addressesJoins = PersonAddressJoin.objects.filter(person=person)
    # addresses = Addresses.objects.filter(address_id__in=addressesJoi
    # ns.values('address_id'))

    # print(test)

    AddressFormSet = modelformset_factory(Addresses, form=AddressesForm, extra=0)
    PhoneFormSet = modelformset_factory(Phones, form=PhoneForm, extra=0)

    NewTestFormSet = modelformset_factory(Tests, form=NewTest, extra=test_extra) #for adding new tests if needed
    EmailFormSet = modelformset_factory(Emails, form=EmailForm, extra=email_extra)

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
        logform = NewTraceLogForm(user, request.POST, instance=log, initial={'notes': log_initial})

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
            # symptomlogform.rec_date = date.today()

        # print("Case: %s | Person: %s | Address: %s | Phone: %s | Email: %s | Test: %s | Log: %s | Sx: %s" %
        #       (caseform.is_valid(),
        #        personform.is_valid(),
        #        addressforms.is_valid(),
        #        emailforms.is_valid(),
        #        phoneforms.is_valid(),
        #        testforms.is_valid(),
        #        logform.is_valid(),
        #        symptomlogforms.is_valid()))

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

            if caseform.cleaned_data['status'] == Statuses.objects.get(status_id=5) or \
                    caseform.cleaned_data['status'] == Statuses.objects.get(status_id=11) or \
                    caseform.cleaned_data['status'] == Statuses.objects.get(status_id=12) or \
                    caseform.cleaned_data['status'] == Statuses.objects.get(status_id=13) or \
                    caseform.cleaned_data['status'] == Statuses.objects.get(status_id=14) or\
                    caseform.cleaned_data['status'] == Statuses.objects.get(status_id=15) or \
                    caseform.cleaned_data['status'] == Statuses.objects.get(status_id=17) or \
                    caseform.cleaned_data['status'] == Statuses.objects.get(status_id=16):

                # print("Secondary, by status:")
                # print(caseform.cleaned_data['status'])
                this_case.active = False
            elif caseform.cleaned_data['status'] == Statuses.objects.get(status_id=4):
                this_case.hospitalized = True
                this_case.active = True
            else:
                this_case.active = True

            # this_test.save()
            this_person.save()
            this_case.save()

            # print("up to the test section")
            if testforms.has_changed():
                # print("formset has changed")
                for testform in testforms:
                    if testform.has_changed():
                        # print("form has changed")
                        if testform.is_valid():
                            # print("form is valid")
                            this_test = testform.save(commit=False)
                            this_test.user = user
                            this_test.logged_date = date.today()
                            # if this_test.result == TestResults.get(result_id=1):
                            #     if this_test.test_type == TestTypes.get
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
                this_assignment.date_done = date.today()
                this_assignment.save()

            if 'save_and_exit' in request.POST:
                # print('save_exit')
                return redirect('info', cttype=cttype, pid=pid)
            elif 'save_and_add_existing_contacts' in request.POST:
                return redirect('/TracingApp/add-contact-existing/%s/%s' % (cttype, pid))
            elif 'save_and_add_contacts' in request.POST:
                # print('save_contacts')
                return redirect('/TracingApp/add-contact/%s/%s' % (cttype, pid))
            elif 'save_and_link_cases' in request.POST:
                return redirect('new-cluster-from', page='case-investigation', case_id=pid)
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
        logform = NewTraceLogForm(user, instance=log, initial={'notes': log_initial})

        symptomforms = SymptomFormSet(queryset=Symptoms.objects.none(), prefix='symptom')
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

    if pid == 0:
        case = Cases()
    else:
        case = get_object_or_404(Cases, case_id=pid)

    contact = Contacts()
    person = Persons()
    log = TraceLogs()
    exposure = Exposures(exposing_case=case)
    AddressFormSet = modelformset_factory(Addresses, form=AddContactAddress, extra=1)
    PhoneFormSet = modelformset_factory(Phones, form=AddContactPhone, extra=1)
    SymptomLogFormSet = modelformset_factory(SxLog, form=NewSymptomLogForm, extra=1)
    EmailFormSet = modelformset_factory(Emails, form=AddContactEmailForm, extra=1)
    ExposureFormSet = modelformset_factory(Exposures, form=ContactExposureForm, extra=1, can_delete=True)

    addressformhelper = AddContactAddressHelper()
    phoneformhelper = AddContactPhoneHelper()
    emailformhelper = AddContactEmailFormHelper()
    symptomloghelper = SymptomLogSetHelper()
    exposureformhelper = ContactExposureFormSetHelper()

    person_address_query = PersonAddressJoin.objects.none()
    addressquery = Addresses.objects.none()

    person_phone_query = PersonPhoneJoin.objects.none()
    phone_query = Phones.objects.none()
    email_query = Emails.objects.none()

    # case_sx_query = CaseSxJoin.objects.filter(case=case)
    symptom_query = SxLog.objects.none()

    exposure_query = Exposures.objects.none()

    user = AuthUser.objects.get(id=request.user.id)

    if request.method == 'POST':

        contactform = AddContactForm(request.POST, instance=contact)
        personform = PersonForm(request.POST, instance=person)
        logform = ContactTraceLogForm(user, request.POST, instance=log)
        # relationform = AddCaseRelation(request.POST)
        usecasephoneform = AddCasePhoneForContact(request.POST)
        usecaseemailform = AddCaseEmailForContact(request.POST)
        usecaseaddressform = AddCaseAddressForContact(request.POST)

        if pid == 0:
            usecasephoneform.fields['use_case_phone'].disabled = True
            usecaseemailform.fields['use_case_email'].disabled = True
            usecaseaddressform.fields['use_case_address'].disabled = True
            contactform.fields['copy_case_notes'].disabled = True

        addressforms = AddressFormSet(request.POST, prefix='address')
        phoneforms = PhoneFormSet(request.POST, prefix='phone')
        emailforms = EmailFormSet(request.POST, prefix='email')
        exposureforms = ExposureFormSet(request.POST, initial=[{'exposing_case': case}], prefix='exposure')

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
                and usecasephoneform.is_valid() \
                and usecaseemailform.is_valid() \
                and usecaseaddressform.is_valid() \
                and emailforms.is_valid() \
                and addressforms.is_valid() \
                and phoneforms.is_valid() \
                and symptomlogforms.is_valid() \
                and exposureforms.is_valid():

            this_person = personform.save()
            # print(contactform.cleaned_data)

            if contactform.cleaned_data['mark_as_contacted']:
                contactform.cleaned_data['last_follow'] = date.today()

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

            # relation = relationform.cleaned_data['relation_to_case']
            for exposureform in exposureforms:
                if exposureform.is_valid():
                    try:
                        if not exposureform.cleaned_data['DELETE']:
                            exposure = exposureform.save()
                            if exposure.exposing_case is None and pid != 0:
                                exposure.relation_to_case = 'Unknown'
                                exposure.exposing_case = case
                                exposure.save()
                            contact_exposure = ContactExposureJoin(contact=this_contact, exposure=exposure)
                            contact_exposure.save()
                    except KeyError:
                        exposure = exposureform.save()
                        if exposure.exposing_case is None and pid != 0:
                            exposure.relation_to_case = 'Unknown'
                            exposure.exposing_case = case
                            exposure.save()
                        contact_exposure = ContactExposureJoin(contact=this_contact, exposure=exposure)
                        contact_exposure.save()

            # case_contact, ctd = CaseContactJoin.objects.get_or_create(case=case,
            #                                                           contact=this_contact,
            #                                                           relation_to_case=relation)
            # case_contact.save()

            if usecaseaddressform.cleaned_data['use_case_address']:
                case_address = PersonAddressJoin.objects.filter(person=case.person).first().address
                person_address, created2 = PersonAddressJoin.objects.get_or_create(person=this_person, address=case_address)
                person_address.save()

            for addressform in addressforms:
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

            if usecaseemailform.cleaned_data['use_case_email']:
                case_email = PersonEmailJoin.objects.filter(person=case.person).first().email
                person_email, created2 = PersonEmailJoin.objects.get_or_create(person=this_person, email=case_email)
                person_email.save()

            for emailform in emailforms:
                if emailform.is_valid():
                    this_email = emailform.save()
                    person_email, created3 = PersonEmailJoin.objects.get_or_create(person=this_person, email=this_email)
                    person_email.save()
                    # this_phone.save()

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

            if contactform.cleaned_data['status'] == Statuses.objects.get(status_id=9) or \
                    contactform.cleaned_data['status'] == Statuses.objects.get(status_id=10):

                # print("Caseform changed and marked as case")
                this_contact.active = False
                # print("Just set to inactive, is it?")
                # print(this_caseform.active)

                # print(caseform.cleaned_data['active'])
                this_status = contactform.cleaned_data['status']
                today = date.today()

                upgraded_case = Cases(person=this_person,
                                      status=this_status,
                                      last_follow=today,
                                      active=1,
                                      )

                if contactform.cleaned_data['status'] == Statuses.objects.get(status_id=9):
                    upgraded_case.probable = True

                upgraded_case.save()
                this_contact.upgraded_case = upgraded_case
                this_contact.save()
                # print("UPGRADED YET? %s" % this_caseform.upgraded_case)

                old_tests = ContactTestJoin.objects.filter(contact=this_contact)

                for old_test in old_tests:
                    transfer_test = CaseTestJoin(case=upgraded_case,
                                                 test=old_test.test)
                    transfer_test.save()

                all_symptoms = ContactSxJoin.objects.filter(case=this_contact).values('sx_id')
                for symptom in all_symptoms:
                    # current_symptom = SxLog.objects.get(log_id=symptom)
                    case_sx = CaseSxJoin(case=upgraded_case, sx_id=symptom['sx_id'])
                    case_sx.save()

                note_data = {'contact': this_contact.contact_id,
                             'date': today,
                             'case': upgraded_case.case_id,
                             'status': this_status,
                             }
                note = 'Contact CT{contact} has been {status}. New ID is C{case}.'.format(**note_data)
                upgrade_log = TraceLogs(notes=note, user=user, log_date=today)
                this_new_log = upgrade_log.save()
                contact_log2 = ContactLogJoin(contact=this_contact, log=upgrade_log)
                contact_log2.save()

                all_logs = ContactLogJoin.objects.filter(contact=this_contact).values('log_id')
                for log in all_logs:
                    new_case_log = CaseLogJoin(case=upgraded_case, log_id=log['log_id'])
                    new_case_log.save()

                linked_exposures = ContactExposureJoin.objects.filter(contact=this_contact).values("exposure_id")
                # print("Linked exposures: %s" % linked_exposures)
                linked_cases = Exposures.objects.filter(exposure_id__in=linked_exposures)
                # print("Linked cases: %s" % linked_cases)

                for linked_case in linked_cases:

                    if linked_case.exposing_case:
                        new_cluster = Clusters()
                        new_cluster.save()
                        print("Linked case: %s" % linked_case.exposing_case)

                        this_link = ClusterCaseJoin(cluster=new_cluster,
                                                    index_case=linked_case.exposing_case,
                                                    case=linked_case.exposing_case,
                                                    )
                        upgraded_case_cluster_link = ClusterCaseJoin(cluster=new_cluster,
                                                                     case=upgraded_case,
                                                                     index_case=linked_case.exposing_case,
                                                                     associated_contact=this_contact,
                                                                     last_exposed=linked_case.last_exposure,
                                                                     )

                        this_link.save()
                        upgraded_case_cluster_link.save()

            elif contactform.cleaned_data['status'] == Statuses.objects.get(status_id=5) or \
                    contactform.cleaned_data['status'] == Statuses.objects.get(status_id=11) or \
                    contactform.cleaned_data['status'] == Statuses.objects.get(status_id=12) or \
                    contactform.cleaned_data['status'] == Statuses.objects.get(status_id=13) or \
                    contactform.cleaned_data['status'] == Statuses.objects.get(status_id=14) or \
                    contactform.cleaned_data['status'] == Statuses.objects.get(status_id=15) or \
                    contactform.cleaned_data['status'] == Statuses.objects.get(status_id=17) or \
                    contactform.cleaned_data['status'] == Statuses.objects.get(status_id=16):

                # print("Secondary, by status:")
                # print(caseform.cleaned_data['status'])
                this_contact.active = False
                this_contact.save()
            else:
                this_contact.active = True
                this_contact.save()

            if pid != 0:
                messages.success(request, "Contact CT%s:%s %s added to Case C%s." % (this_contact.contact_id,
                                                                                     this_person.first,
                                                                                     this_person.last,
                                                                                     case.case_id))
            else:
                messages.success(request, "Contact CT%s:%s %s added to database." % (this_contact.contact_id,
                                                                                     this_person.first,
                                                                                     this_person.last))

            if 'save_and_exit' in request.POST:
                if pid != 0:
                    return redirect('info', cttype=cttype, pid=pid)
                else:
                    return redirect('info', cttype='CT', pid=this_contact.contact_id)
            elif 'save_and_add_another' in request.POST:
                return redirect('/TracingApp/add-contact/%s/%s' % (cttype, pid))
            else:
                return redirect('assignments')

    else:
        personform = PersonForm(instance=person)
        # relationform = AddCaseRelation()
        usecasephoneform = AddCasePhoneForContact()
        usecaseemailform = AddCaseEmailForContact()
        usecaseaddressform = AddCaseAddressForContact()

        addressforms = AddressFormSet(queryset=addressquery, prefix='address')
        # phonequery = PersonPhoneJoin.objects.filter(person_id=case.person_id)
        phoneforms = PhoneFormSet(queryset=phone_query, prefix='phone')
        emailforms = EmailFormSet(queryset=email_query, prefix='email')
        # print(case)
        exposureforms = ExposureFormSet(queryset=exposure_query, initial=[{'exposing_case': case}], prefix='exposure')
        # print(exposureforms)
        contactform = AddContactForm(instance=contact)
        logform = ContactTraceLogForm(user, instance=log)

        symptomlogforms = SymptomLogFormSet(queryset=symptom_query, prefix='sxlog')

        if pid == 0:
            usecasephoneform.fields['use_case_phone'].disabled = True
            usecaseemailform.fields['use_case_email'].disabled = True
            usecaseaddressform.fields['use_case_address'].disabled = True
            contactform.fields['copy_case_notes'].disabled = True

    return render(request, 'contacts/add-contact.html', {'contactform': contactform,
                                                         'personform': personform,
                                                         # 'relationform': relationform,
                                                         'addressforms': addressforms,
                                                         'addressformhelper': addressformhelper,
                                                         'usecasephoneform': usecasephoneform,
                                                         'usecaseemailform': usecaseemailform,
                                                         'usecaseaddressform': usecaseaddressform,
                                                         'phoneforms': phoneforms,
                                                         'phoneformhelper': phoneformhelper,
                                                         'emailforms': emailforms,
                                                         'emailformhelper': emailformhelper,
                                                         'symptomlogforms': symptomlogforms,
                                                         'symptomloghelper': symptomloghelper,
                                                         'logform': logform,
                                                         'exposureforms': exposureforms,
                                                         'exposureformhelper': exposureformhelper,
                                                         })


@login_required(login_url='/accounts/login/')
def followup(request, cttype, pid):

    pending = AssignmentStatus.objects.get(status_id=1)

    if request.user.groups.filter(name='admin_user').exists():
        edit_allowed = True
    else:
        edit_allowed = False

    storage = messages.get_messages(request)
    log_initial = []
    for message in storage:
        log_initial.append("<<Link created>> %s" % message)
    log_initial = str(log_initial).strip('[]').replace("'", "")
    # print(log_initial)

    if cttype == 'C':
        case = get_object_or_404(Cases, case_id=pid)
        symptom_query = CaseSxJoin.objects.filter(case_id=case)
        trace_log_query = CaseLogJoin.objects.filter(case_id=case)
        # trace_log_edits = LogEdits.objects.filter(log_id__in=trace_log_query.values('log_id'))
        test = case.test_id
        test_query = CaseTestJoin.objects.filter(case_id=case)
        user = AuthUser.objects.get(id=request.user.id)
        this_assignment, a_created = Assignments.objects.get_or_create(case=case, user=user, status=pending)
        exposures = None
        upgraded_case = None
    elif cttype == 'CT':
        case = get_object_or_404(Contacts, contact_id=pid)
        symptom_query = ContactSxJoin.objects.filter(case_id=case)
        trace_log_query = ContactLogJoin.objects.filter(contact_id=case)
        # trace_log_edits = LogEdits.objects.filter(log_id__in=trace_log_query.values('log_id'))
        test = 0
        test_query = ContactTestJoin.objects.filter(contact_id=case)
        user = AuthUser.objects.get(id=request.user.id)
        this_assignment, a_created = Assignments.objects.get_or_create(contact=case, user=user, status=pending)
        exposures = ContactExposureJoin.objects.filter(contact=case).values('exposure')
        upgraded_case = case.upgraded_case
    else:
        return Http404("Invalid type.")

    trace_log_edits = LogEdits.objects.filter(log_id__in=trace_log_query.values('log_id'))
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
    ContactExposureFormSet = modelformset_factory(Exposures, form=ContactExposureForm, extra=0, can_delete=True)

    new_log = TraceLogs()
    NewSymptomFormSet = modelformset_factory(SxLog, form=NewSymptomLogForm, extra=1)
    # NewTraceLogFormSet = modelformset_factory(TraceLogs, form=NewTraceLogForm, extra=1)

    addressformhelper = AddressesFormHelper()
    phoneformhelper = PhoneFormHelper()
    emailformhelper = EmailFormHelper()
    symptomloghelper = SymptomLogSetHelper()
    traceloghelper = OldTraceLogFormHelper()
    testformhelper = NewTestFormHelper()
    contactexposureformhelper = ContactExposureFormSetHelper()

    if symptom_query.count() == 0:
        symptomforms = None
    else:
        symptomforms = SymptomFormSet(prefix='oldsx',
                                      queryset=SxLog.objects.filter(log_id__in=symptom_query.values('sx_id')).order_by(
                                          'symptom'))

    if trace_log_query.count() == 0:
        tracelogforms = None
    else:
        tracelogforms = TraceLogFormSet(prefix='oldlogs',
                                        queryset=TraceLogs.objects.filter(log_id__in=trace_log_query.values('log')))

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

        # if symptom_query.count() == 0:
        #     symptomforms = None
        # else:
        #     symptomforms = SymptomFormSet(request.POST, prefix='oldsx', queryset=SxLog.objects.filter(log_id__in=symptom_query.values('sx_id')).order_by('symptom'))
        #
        # if trace_log_query.count() == 0:
        #     tracelogforms = None
        # else:
        #     tracelogforms = TraceLogFormSet(request.POST, prefix='oldlogs', queryset=TraceLogs.objects.filter(log_id__in=trace_log_query.values('log')))
        new_tracelogform = ContactTraceLogForm(user, request.POST, instance=new_log, initial={'notes': log_initial})
        new_symptomforms = NewSymptomFormSet(request.POST, prefix='sxlog',
                                             queryset=SxLog.objects.none())
        newtestforms = TestFormSet(request.POST, queryset=test_query, prefix='new_test')
        if cttype == 'CT':
            contactexposureforms = ContactExposureFormSet(request.POST, queryset=Exposures.objects.filter(exposure_id__in=exposures), prefix='exposure')
        else:
            # contactexposureforms = ContactExposureFormSet(request.POST, queryset=Exposures.objects.none(), prefix='exposure')
            contactexposureforms = None
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

        # print("Case: %s" % caseform.is_valid())
        # print("Person: %s" % personform.is_valid())
        # print("Email: %s" % emailforms.is_valid())
        # print("Address: %s" % addressforms.is_valid())
        # print("Phone: %s" % phoneforms.is_valid())
        # print("Log: %s" % new_tracelogform.is_valid())
        # print("Symptom: %s" % new_symptomforms.is_valid())
        #
        # print(addressforms.errors)

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

            if cttype == 'CT':
                for contactexposureform in contactexposureforms:
                    print(contactexposureform)
                    if contactexposureform.is_valid():
                        this_exposure = contactexposureform.save()
                        contact_exposure_link, ce_created = ContactExposureJoin.objects.update_or_create(contact=case,
                                                                                                         exposure=this_exposure)
                        if ce_created:
                            contact_exposure_link.save()

            for addressform in addressforms:
                if addressform.has_changed():
                    if addressform.is_valid():
                        this_address = addressform.save()
                        person_address, created = PersonAddressJoin.objects.update_or_create(person=this_person,
                                                                                             address=this_address)
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

            this_test = None

            for newtestform in newtestforms:
                if newtestform.has_changed():
                    if newtestform.is_valid():
                        this_test = newtestform.save(commit=False)
                        this_test.user = user
                        this_test.logged_date = date.today()
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

            # print("Caseform chanaged?")
            # print(caseform.changed_data)
            #
            # print("last_follow initial: %s | last_follow current: %s" % (caseform['last_follow'].initial, caseform.cleaned_data['last_follow']))
            # print("active initial: %s | active current: %s" % (
            # caseform['active'].initial, caseform.cleaned_data['active']))

            this_caseform = caseform.save(commit=False)
            this_caseform.upgraded_case = upgraded_case

            if caseform.has_changed():
                # print("It's changed")
                if caseform.cleaned_data['status'] == Statuses.objects.get(status_id=9) or \
                        caseform.cleaned_data['status'] == Statuses.objects.get(status_id=10):
                    # print("It's a contact")
                    # print(caseform.cleaned_data['status'])
                    if cttype == 'CT':
                        # print("UPGRADE? %s" % upgraded_case)
                        if upgraded_case is None:
                            # print("Caseform changed and marked as case")
                            this_caseform.active = False
                            # print("Just set to inactive, is it?")
                            # print(this_caseform.active)

                            # print(caseform.cleaned_data['active'])
                            this_status = caseform.cleaned_data['status']
                            today = date.today()

                            upgraded_case = Cases(person=this_person,
                                                  status=this_status,
                                                  last_follow=today,
                                                  active=1,
                                                  )

                            if caseform.cleaned_data['status'] == Statuses.objects.get(status_id=9):
                                upgraded_case.probable = True

                            upgraded_case.save()
                            this_caseform.upgraded_case = upgraded_case
                            # print("UPGRADED YET? %s" % this_caseform.upgraded_case)

                            old_tests = ContactTestJoin.objects.filter(contact=case)

                            for old_test in old_tests:
                                transfer_test = CaseTestJoin(case=upgraded_case,
                                                             test=old_test.test)
                                transfer_test.save()

                            if this_test is not None:
                                upgraded_case_test_link = CaseTestJoin(case=upgraded_case,
                                                                       test=this_test)
                                upgraded_case_test_link.save()

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

                            linked_exposures = ContactExposureJoin.objects.filter(contact=case).values("exposure_id")
                            print("Linked exposures: %s" % linked_exposures)
                            linked_cases = Exposures.objects.filter(exposure_id__in=linked_exposures)
                            print("Linked cases: %s" % linked_cases)

                            for linked_case in linked_cases:

                                if linked_case.exposing_case:

                                    new_cluster = Clusters()
                                    new_cluster.save()
                                    print("Linked case: %s" % linked_case.exposing_case)

                                    this_link = ClusterCaseJoin(cluster=new_cluster,
                                                                index_case=linked_case.exposing_case,
                                                                case=linked_case.exposing_case,
                                                                )
                                    upgraded_case_cluster_link = ClusterCaseJoin(cluster=new_cluster,
                                                                                 case=upgraded_case,
                                                                                 index_case=linked_case.exposing_case,
                                                                                 associated_contact=this_caseform,
                                                                                 last_exposed=linked_case.last_exposure,
                                                                                 )

                                    this_link.save()
                                    upgraded_case_cluster_link.save()

                elif caseform.cleaned_data['status'] == Statuses.objects.get(status_id=5) or \
                        caseform.cleaned_data['status'] == Statuses.objects.get(status_id=11) or\
                        caseform.cleaned_data['status'] == Statuses.objects.get(status_id=12) or\
                        caseform.cleaned_data['status'] == Statuses.objects.get(status_id=13) or\
                        caseform.cleaned_data['status'] == Statuses.objects.get(status_id=14) or\
                        caseform.cleaned_data['status'] == Statuses.objects.get(status_id=15) or \
                        caseform.cleaned_data['status'] == Statuses.objects.get(status_id=17) or \
                        caseform.cleaned_data['status'] == Statuses.objects.get(status_id=16):

                    # print("Secondary, by status:")
                    # print(caseform.cleaned_data['status'])
                    this_caseform.active = False
                elif caseform.cleaned_data['status'] == Statuses.objects.get(status_id=4):
                    this_caseform.hospitalized = True
                    this_caseform.active = True
                else:
                    this_caseform.active = True

                        # print("Case upgraded")

            # print('Active: %s' % caseform.cleaned_data['active'])
            this_caseform.last_follow = date.today()
            # caseform.cleaned_data['last_follow'] = date.today()
            # print("Before caseform is saved, inactive?")
            # print(this_caseform.active)
            this_caseform.save()

            done_status = AssignmentStatus.objects.get(status_id=2)

            if a_created:
                this_assignment.assign_type = 4
            this_assignment.status = done_status
            this_assignment.date_done = date.today()
            this_assignment.save()

            if 'save_and_exit' in request.POST:
                # print('save_exit')
                return redirect('info', cttype=cttype, pid=pid)
            elif 'save_and_add_existing_contacts' in request.POST:
                return redirect('/TracingApp/add-contact-existing/%s/%s' % (cttype, pid))
            elif 'save_and_add_contacts' in request.POST:
                # print('save_contacts')
                return redirect('/TracingApp/add-contact/%s/%s' % (cttype, pid))
            elif 'save_and_link_cases' in request.POST:
                return redirect('new-cluster-from',  page='follow-up', case_id=pid)
            else:
                return redirect('assignments')

        else:
            print(f'CaseForm: {caseform.errors}')
            print(f'PersonForm: {personform.errors}')
            print(f'EmailForm: {emailforms.errors}')
            print(f'AddressForm: {addressforms.errors}')
            print(f'NewTestForm: {newtestforms.errors}')
            print(f'PhoneForm: {phoneforms.errors}')
            print(f'NewTraceLog: {new_tracelogform.errors}')
            print(f'NewSymptomForm: {new_symptomforms.errors}')

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
        # if symptom_query.count() == 0:
        #     symptomforms = None
        # else:
        #     symptomforms = SymptomFormSet(prefix='oldsx', queryset=SxLog.objects.filter(log_id__in=symptom_query.values('sx_id')).order_by('symptom'))
        # # print(symptom_query)
        # # print("FORMS:")
        # # print(symptomforms)
        # if trace_log_query.count() == 0:
        #     tracelogforms = None
        # else:
        #     tracelogforms = TraceLogFormSet(prefix='oldlogs', queryset=TraceLogs.objects.filter(log_id__in=trace_log_query.values('log')))
        new_tracelogform = ContactTraceLogForm(user, instance=new_log, initial={'notes': log_initial})
        new_symptomforms = NewSymptomFormSet(prefix='sxlog',
                                             queryset=SxLog.objects.none())
        newtestforms = TestFormSet(prefix='new_test', queryset=test_query)
        if exposures is not None:
            contactexposureforms = ContactExposureFormSet(queryset=Exposures.objects.filter(exposure_id__in=exposures),
                                                          prefix='exposure')
        else:
            # contactexposureforms = ContactExposureFormSet(queryset=Exposures.objects.none(),
            #                                               prefix='exposure')
            contactexposureforms = None

        # print(test_query)
        # A contact shouldn't have a test
        testforms = Tests.objects.none()

        print(f'Trace edits: {trace_log_edits.values("previous_text")}')

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
                                              'exposureforms': contactexposureforms,
                                              'exposureformhelper': contactexposureformhelper,
                                              'pid': pid,
                                              'tracelogedits': trace_log_edits,
                                              'edit_allowed': edit_allowed,
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
                    # print(caseassign.cleaned_data)
                    if caseassign.cleaned_data['assign_box']:
                        # print('checked box')
                        user_assigned = assignform.cleaned_data['user']
                        if user_assigned is not None and user_assigned != AuthUser.objects.get(id=1):
                            this_assign = Assignments(user=user_assigned,
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
        # print(caseassignments.errors)

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
def create_cluster(request):

    if request.method == 'POST':

        caselinkform = CaseLinkForm(request.POST)
        # caselinkform.fields['cases'].initial = Cases.objects.get(case_id=case_id)

        # print("HH form valid?")
        # print(householdform.is_valid())
        if caselinkform.is_valid():
            cases = caselinkform.cleaned_data['cases']

            this_cluster = Clusters()
            this_cluster.save()

            for case in cases:
                # print(person.person_id)
                this_cluster_case = ClusterCaseJoin(cluster=this_cluster, case=case)
                this_cluster_case.save()

            if 'continue' in request.POST:
                # print('save_exit')
                return redirect('edit-cluster', cluster_id=this_cluster.cluster_id)
            else:
                return redirect('assignments')

    else:
        caselinkform = CaseLinkForm()
        # caselinkform.fields['cases'].initial = Cases.objects.get(case_id=case_id)

    return render(request, 'link-cases/link-cases.html', {'caselinkform': caselinkform,
                                                               })


@login_required(login_url='/accounts/login/')
def create_cluster_from(request, page, case_id):

    if request.method == 'POST':

        caselinkform = CaseLinkForm(request.POST)
        caselinkform.fields['cases'].initial = Cases.objects.get(case_id=case_id)

        # print("HH form valid?")
        # print(householdform.is_valid())
        if caselinkform.is_valid():
            cases = caselinkform.cleaned_data['cases']

            this_cluster = Clusters()
            this_cluster.save()

            for case in cases:
                # print(person.person_id)
                this_cluster_case = ClusterCaseJoin(cluster=this_cluster, case=case)
                this_cluster_case.save()

            if 'continue' in request.POST:
                # print('save_exit')
                return redirect('edit-case-cluster', page=page, case_id=case_id, cluster_id=this_cluster.cluster_id)
            else:
                return redirect(page, cttype='C', pid=case_id)

    else:
        caselinkform = CaseLinkForm()
        caselinkform.fields['cases'].initial = Cases.objects.get(case_id=case_id)

    return render(request, 'link-cases/link-cases.html', {'caselinkform': caselinkform,
                                                               })


@login_required(login_url='/accounts/login/')
def edit_cluster(request, cluster_id):
    # Get the cluster object or throw a 404 if it doesn't exist
    cluster = get_object_or_404(Clusters, cluster_id=cluster_id)

    # Get the index case to use to have a radio button pre-selected
    # try:
    #     selected = ClusterCaseJoin.objects.filter(cluster=cluster).first().index_case
    # except ClusterCaseJoin.DoesNotExist:
    #     selected = None

    ClusterFormset = modelformset_factory(ClusterCaseJoin, form=ClusterEditForm, extra=0, can_delete=True)
    ClusterCaseQS = ClusterCaseJoin.objects.filter(cluster=cluster)

    # print(cluster.cluster_id)
    # print(selected)

    # Enter the section governed by a POST request
    if request.method == 'POST':
        editclusterforms = ClusterFormset(request.POST, queryset=ClusterCaseQS, prefix='cluster')

        # print(editclusterforms.is_valid())
        # print(editclusterforms.errors)

        # Check the validity of the form
        index_case_id = None

        if editclusterforms.is_valid():

            for x in editclusterforms:
                if x.is_valid():
                    if x.cleaned_data['is_index'] and index_case_id is None:
                        index_case_id = x.cleaned_data['case']
                        # print("Index: %s" % index_case_id)

            for clusterform in editclusterforms:
                # if clusterform.is_valid():
                clusterform.instance.index_case = index_case_id
                # clusterform.cleaned_data['details'] = "TESTING"
                # print("Index case set to: %s" % clusterform.cleaned_data['index_case'])
                clusterform.save()
                # print("Cleaned data: %s" % clusterform.cleaned_data['index_case'])

            for deleted in editclusterforms.deleted_forms:
                # print(deleted)
                case = deleted.instance.case
                cluster = Clusters.objects.get(cluster_id=cluster_id)
                ClusterCaseJoin.objects.get(case=case, cluster=cluster).delete()
                messages.success(request, "Case %s removed from cluster %s." % (case.case_id, cluster_id))

            remaining_cases = len(ClusterCaseJoin.objects.filter(cluster=cluster))
            # print(remaining_cases)
            if remaining_cases == 0:
                cluster.delete()
                messages.success(request, "Cluster %s is empty and has been deleted." % cluster_id)

            if 'save_and_exit' in request.POST:
                # print('save_exit')
                messages.success(request, "Case %s set as the index for cluster %s." % (index_case_id, cluster_id))
                return redirect('info', cttype='C', pid=index_case_id.case_id)
            else:
                ClusterCaseJoin.objects.filter(cluster=cluster).delete()
                cluster.delete()
                return redirect('assignments')

        else:
            messages.error(request, "You must select an index case for this cluster.")
    else:
        editclusterforms = ClusterFormset(queryset=ClusterCaseQS, prefix='cluster')
        # if selected:
        #     editclusterforms = ClusterFormset(queryset=ClusterCaseQS, initial={'case': selected.case_id})
        #     # editclusterform = ClusterEditForm(instance=cluster, initial={'case': selected.case_id})
        # else:
        #     editclusterforms = ClusterFormset(queryset=ClusterCaseQS, prefix='cluster')
        #     # editclusterform = ClusterEditForm(instance=cluster)
        # # print(editclusterform)
        return render(request, 'link-cases/edit-cluster.html', {'editclusterforms': editclusterforms,
                                                          })


@login_required(login_url='/accounts/login/')
def edit_case_cluster(request, page, case_id, cluster_id):
    # Get the cluster object or throw a 404 if it doesn't exist
    cluster = get_object_or_404(Clusters, cluster_id=cluster_id)
    this_case_id = case_id

    # Get the index case to use to have a radio button pre-selected
    try:
        selected = ClusterCaseJoin.objects.filter(cluster=cluster).first().index_case
    except ClusterCaseJoin.DoesNotExist:
        selected = None

    ClusterFormset = modelformset_factory(ClusterCaseJoin, form=ClusterEditForm, extra=0, can_delete=True)
    ClusterCaseQS = ClusterCaseJoin.objects.filter(cluster=cluster)

    # print(cluster.cluster_id)
    # print(selected)

    # Enter the section governed by a POST request
    if request.method == 'POST':
        editclusterforms = ClusterFormset(request.POST, queryset=ClusterCaseQS, prefix='cluster')

        # print(editclusterforms.is_valid())
        # print(editclusterforms.errors)

        # Check the validity of the form
        index_case_id = None

        if editclusterforms.is_valid():

            for x in editclusterforms:
                if x.is_valid():
                    if x.cleaned_data['is_index'] and index_case_id is None:
                        index_case_id = x.cleaned_data['case']
                        # print("Index: %s" % index_case_id)

            for clusterform in editclusterforms:
                # if clusterform.is_valid():
                clusterform.instance.index_case = index_case_id
                # clusterform.cleaned_data['details'] = "TESTING"
                # print("Index case set to: %s" % clusterform.cleaned_data['index_case'])
                clusterform.save()
                # print("Cleaned data: %s" % clusterform.cleaned_data['index_case'])

            for deleted in editclusterforms.deleted_forms:
                # print(deleted)
                case = deleted.instance.case
                cluster = Clusters.objects.get(cluster_id=cluster_id)
                ClusterCaseJoin.objects.get(case=case, cluster=cluster).delete()
                messages.success(request, "Case %s removed from cluster %s." % (case.case_id, cluster_id))

            remaining_cases = len(ClusterCaseJoin.objects.filter(cluster=cluster))
            # print(remaining_cases)
            if remaining_cases == 0:
                cluster.delete()
                messages.success(request, "Cluster %s is empty and has been deleted." % cluster_id)

            if 'save_and_exit' in request.POST:
                # print('save_exit')
                messages.success(request, "Case %s set as the index for cluster %s." % (index_case_id, cluster_id))
                return redirect(page, cttype='C', pid=this_case_id)
            else:
                ClusterCaseJoin.objects.filter(cluster=cluster).delete()
                cluster.delete()
                return redirect('assignments')

        else:
            messages.error(request, "You must select an index case for this cluster.")
    else:
        editclusterforms = ClusterFormset(queryset=ClusterCaseQS, prefix='cluster')
        # if selected:
        #     editclusterforms = ClusterFormset(queryset=ClusterCaseQS, initial={'case': selected.case_id})
        #     # editclusterform = ClusterEditForm(instance=cluster, initial={'case': selected.case_id})
        # else:
        #     editclusterforms = ClusterFormset(queryset=ClusterCaseQS, prefix='cluster')
        #     # editclusterform = ClusterEditForm(instance=cluster)
        # # print(editclusterform)
        return render(request, 'link-cases/edit-cluster.html', {'editclusterforms': editclusterforms,
                                                          })

@login_required(login_url='/accounts/login/')
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        # print(form.is_valid())
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
    queries = request.GET.get('q').split()
    print(queries)

    import functools
    import operator

    qset = functools.reduce(operator.__or__, [Q(last__icontains=query) | Q(first__icontains=query) for query in queries])
    persons = Persons.objects.filter(qset)
    cases_p = None
    contacts_p = None
    cases = None
    contacts = None

    # print(persons)

    if persons:
        cases_p = Cases.objects.filter(person_id__in=persons)
        contacts_p = Contacts.objects.filter(person_id__in=persons)

    # print(cases_p)
    is_case = False
    is_contact = False
    is_probable = False
    for query in queries:
        is_case = re.search('C\d+', query) or is_case
        is_contact = re.search('CT\d+', query) or is_contact
        is_probable = re.search('P\d+', query) or is_probable

    # print(is_case)

    if is_case or is_probable:
        case_queries = []
        for query in queries:
            case_queries.append(re.findall('\d+', query)[0])
        qset2 = functools.reduce(operator.__or__, [Q(case_id=case_query) | Q(old_case_no="C%s" % case_query) | Q(old_case_no="P%s" % case_query) for case_query in case_queries])
        cases = Cases.objects.filter(qset2)
    elif is_contact:
        contact_queries = []
        for query in queries:
            contact_queries.append(re.findall('\d+', query)[0])
        qset3 = functools.reduce(operator.__or__, [Q(contact_id=contact_query) | Q(old_contact_no="CT%s" % contact_query) for contact_query in contact_queries])
        # print(contact_query)
        contacts = Contacts.objects.filter(qset3)
    elif is_probable:
        case_queries = []
        for query in queries:
            case_queries.append(re.findall('\d+', query)[0])
        qset4 = functools.reduce(operator.__or__, [Q(old_case_no="P%s" % case_query) for case_query in case_queries])
        # case_query = re.findall('\d+', query)
        cases = Cases.objects.filter(qset4)
    elif len(persons) == 0:
        case_queries = []
        for query in queries:
            reg = re.findall('\d+', query)
            print(reg)
            if len(reg) > 0:
                case_queries.append(reg[0])

        print(case_queries)
        if len(case_queries) > 0:
            qset5 = functools.reduce(operator.__or__, [Q(case_id=case_query) | Q(old_case_no="C%s" % case_query) for case_query in case_queries])
            qset6 = functools.reduce(operator.__or__, [Q(contact_id=case_query) | Q(old_contact_no="CT%s" % case_query) for case_query in case_queries])
            cases = Cases.objects.filter(qset5)
            contacts = Contacts.objects.filter(qset6)

    return render(request, 'search.html', {'cases_p': cases_p,
                                           'contacts_p': contacts_p,
                                           'cases': cases,
                                           'contacts': contacts,
                                           })


@login_required(login_url='/accounts/login/')
def new_outbreak(request):

    LocationPhoneFormSet = modelformset_factory(Phones, form=NewPhoneNumberForm, extra=1)

    locationaddress = Addresses()
    location = Locations()
    outbreak = Outbreaks()

    if request.method == "POST":

        locationform = NewLocation(request.POST, instance=location)
        phoneforms = LocationPhoneFormSet(request.POST, prefix='phone')
        locationaddressform = NewAddressForm(request.POST, instance=locationaddress)
        outbreakform = NewOutbreakForm(request.POST, instance=outbreak)


    else:

        locationform = NewLocation(instance=location)
        phoneforms = LocationPhoneFormSet(prefix='phone')
        locationaddressform = NewAddressForm(instance=locationaddress)
        outbreakform = NewOutbreakForm(instance=outbreak)

        return render(request, 'outbreaks/new-outbreak.html', {'locationform': locationform,
                                                               'phoneforms': phoneforms,
                                                               'locationaddressform': locationaddressform,
                                                               'outbreakform': outbreakform,
                                                               })


@login_required(login_url='/accounts/login/')
def add_existing_contact(request,cttype, case_id):

    if request.method == 'POST':

        contactlinkform = ContactBulkForm(request.POST)
        # caselinkform.fields['cases'].initial = Cases.objects.get(case_id=case_id)

        # print("HH form valid?")
        # print(householdform.is_valid())
        if contactlinkform.is_valid():
            contacts = contactlinkform.cleaned_data['contacts']

            exposure_list = []

            for contact in contacts:
                # print(person.person_id)
                this_exposure = Exposures(exposing_case_id=case_id)
                this_exposure.save()

                exposure_contact = ContactExposureJoin(contact=contact, exposure=this_exposure)
                exposure_contact.save()
                exposure_list.append(exposure_contact.exposure_id)

            if 'continue' in request.POST:
                # print('save_exit')
                return redirect('edit-bulk-contacts', cttype=cttype, case_id=case_id, contact_list=exposure_list)
            else:
                return redirect('case-investigation', cttype=cttype, pid=case_id)

    else:
        contactlinkform = ContactBulkForm()
        # caselinkform.fields['cases'].initial = Cases.objects.get(case_id=case_id)

    return render(request, 'contacts/bulk-add-contact.html', {'contactlinkform': contactlinkform,
                                                              })


@login_required(login_url='/accounts/login/')
def edit_bulk_contacts(request, cttype, case_id, contact_list):

    contact_list = contact_list[1:(len(contact_list)-1)]
    contact_list = contact_list.replace(" ", "")
    contact_list = contact_list.split(",")
    # print(contact_list)
    contact_query = ContactExposureJoin.objects.filter(exposure_id__in=contact_list)
    exposure_query = Exposures.objects.filter(exposure_id__in=contact_list)
    # print(contact_query)
    ContactFormSet = modelformset_factory(Exposures, form=ContactBulkEditForm, extra=0)

    # print(contact_query)
    # print(exposure_query)

    contactformhelper = ContactBulkEditFormHelper()

    if request.method == 'POST':
        contactforms = ContactFormSet(request.POST,
                                      queryset=exposure_query,
                                      prefix="exposure")

        if contactforms.is_valid():

            for contactform in contactforms:
                if contactform.is_valid():
                    contactform.save()
                    messages.success(request, '%s linked to case C%s.' % (contactform.cleaned_data['name'], case_id))

            if 'save_and_exit' in request.POST:
                # print('save_exit')
                return redirect('case-investigation', cttype=cttype, pid=case_id)
            else:
                return redirect('case-investigation', cttype=cttype, pid=case_id)

    else:
        contactforms = ContactFormSet(queryset=exposure_query,
                                      prefix="exposure")

    return render(request, 'contacts/bulk-edit-contacts.html', {'contactforms': contactforms,
                                                              'contactformhelper': contactformhelper,
                                                              })


@login_required(login_url='/accounts/login/')
def case_import(request):
    from django.utils.datastructures import MultiValueDictKeyError

    template = "import/import_cases.html"
    # data = Cases.objects.all()

    if request.method == "GET":
        return render(request, template)

    try:
        csv_file = request.FILES['file']
    except MultiValueDictKeyError:
        messages.error(request, 'No file selected.')
        return render(request, template)
    csv_file2 = csv_file

    # fuzzy_match(csv_file2)

    if not csv_file.name.endswith('.csv'):
        messages.error(request, 'THIS IS NOT A CSV FILE')
    # data_set = csv.reader(csv_file)
    # data_set = csv.DictReader(csv_file, delimiter=',')
    data_set = csv_file.read().decode('UTF-8')
    # setup a stream which is when we loop through each line we are able to handle a data in a stream
    print("Pre next")
    io_string = io.StringIO(data_set)
    next(io_string)
    print("Post next")
    print(io_string)
    # for line in data_set:
    #     print(line)

    cases_added = []
    row = 0
    date_check = True

    for line in csv.reader(io_string, delimiter=',', quotechar="|"):
        row = row + 1
        print(line)
        # dob = datetime.datetime.strptime("1-1-1900", '%d-%m-%Y')
        dob = line[5]
        sample_date = line[14]
        result_date = line[15]
        rcvd_date = line[16]
        dob_pass = False
        sample_pass = False
        result_pass = False
        rcvd_pass = False
        for fmt in ('%Y-%m-%d', '%d%B%Y', '%d%b%Y', '%m/%d/%Y'):
            try:
                if dob == '':
                    dob = datetime.datetime.strptime("1-1-1900", '%d-%m-%Y')
                else:
                    dob = datetime.datetime.strptime(dob.strip(), fmt)
                dob_pass = True
            except ValueError:
                pass
            except AttributeError:
                pass
            try:
                if sample_date == '' or sample_date is None:
                    sample_date = None
                else:
                    sample_date = datetime.datetime.strptime(sample_date.strip(), fmt)
                sample_pass = True
            except ValueError:
                pass
            except AttributeError:
                pass
            try:
                if result_date == '' or result_date is None:
                    result_date = None
                else:
                    result_date = datetime.datetime.strptime(result_date.strip(), fmt)
                result_pass = True
            except ValueError:
                pass
            except AttributeError:
                pass
            try:
                if rcvd_date == '' or rcvd_date is None:
                    rcvd_date = None
                else:
                    rcvd_date = datetime.datetime.strptime(rcvd_date.strip(), fmt)
                rcvd_pass = True
            except ValueError:
                pass
            except AttributeError:
                pass

        if not (dob_pass and sample_pass and result_pass and rcvd_pass):
            if not dob_pass:
                messages.error(request, 'Check date format for [DOB] in row %s' % row)
            if not sample_pass:
                messages.error(request, 'Check date format for [Sample] in row %s' % row)
            if not result_pass:
                messages.error(request, 'Check date format for [Result] in row %s' % row)
            if not rcvd_pass:
                messages.error(request, 'Check date format for [RCVD] in row %s' % row)
            date_check = False

    if not date_check:
        return render(request, template)
    else:
        io_string.seek(0)
        next(io_string)

    for line in csv.reader(io_string, delimiter=',', quotechar="|"):
        print(line)
        dob = line[5]
        sample_date = line[14]
        result_date = line[15]
        rcvd_date = line[16]

        for fmt in ('%Y-%m-%d', '%d%B%Y', '%d%b%Y', '%m/%d/%Y'):
            try:
                if dob == '':
                    dob = datetime.datetime.strptime("1-1-1900", '%d-%m-%Y')
                elif isinstance(dob, datetime.datetime):
                    pass
                else:
                    dob = datetime.datetime.strptime(dob.strip(), fmt)
            except ValueError:
                pass
            except AttributeError:
                pass
            try:
                if sample_date == '' or sample_date is None:
                    sample_date = None
                elif isinstance(sample_date, datetime.datetime):
                    pass
                else:
                    sample_date = datetime.datetime.strptime(sample_date.strip(), fmt)
            except ValueError:
                pass
            try:
                if result_date == '' or result_date is None:
                    result_date = None
                elif isinstance(result_date, datetime.datetime):
                    pass
                else:
                    result_date = datetime.datetime.strptime(result_date.strip(), fmt)
            except ValueError:
                pass
            try:
                if rcvd_date == '' or rcvd_date is None:
                    rcvd_date = None
                elif isinstance(rcvd_date, datetime.datetime):
                    pass
                else:
                    rcvd_date = datetime.datetime.strptime(rcvd_date.strip(), fmt)
            except ValueError:
                pass

        new_person, created = Persons.objects.update_or_create(
            first=line[0],
            mi=line[1],
            last=line[2],
            suffix=line[3],
            sex=line[4],
            dob=dob,
            # age=column[6],
        )

        if created:

            # sample_date = None
            # result_date = None
            # rcvd_date = None
            # for fmt in ('%Y-%m-%d', '%d%B%Y', '%d%b%Y', '%m/%d/%Y'):
            #     try:
            #         sample_date = line[14]
            #         sample_date = datetime.datetime.strptime(sample_date.strip(), fmt)
            #     except ValueError:
            #         pass
            # for fmt in ('%Y-%m-%d', '%d%B%Y', '%d%b%Y', '%m/%d/%Y'):
            #     try:
            #         result_date = line[15]
            #         result_date = datetime.datetime.strptime(result_date.strip(), fmt)
            #     except ValueError:
            #         pass
            # for fmt in ('%Y-%m-%d', '%d%B%Y', '%d%b%Y', '%m/%d/%Y'):
            #     try:
            #         rcvd_date = line[16]
            #         rcvd_date = datetime.datetime.strptime(rcvd_date.strip(), fmt)
            #     except ValueError:
            #         pass
            # if sample_date is None:
            #     new_person.delete()
            #     messages.error(request, 'Sample Date invalid. Enter a valid date.')
            #     return render(request, template)
            # if result_date is None:
            #     new_person.delete()
            #     messages.error(request, 'Result Date invalid. Enter a valid date.')
            #     return render(request, template)
            # if rcvd_date is None:
            #     new_person.delete()
            #     messages.error(request, 'Received Date invalid. Enter a valid date.')
            #     return render(request, template)

            new_test = Tests(sample_date=sample_date,
                             result_date=result_date,
                             rcvd_date=rcvd_date,
                             test_type=TestTypes.objects.get(test_type_id=line[18]),
                             logged_date=date.today(),
                             user=AuthUser.objects.get(id=request.user.id),
                             result=TestResults.objects.get(result_id=line[17]),
                             source=TestSources.objects.get(id=line[19]),
                             )
            new_test.save()
            print(new_test)

            new_address = Addresses(street=line[7],
                                    street2=line[8],
                                    city=line[9],
                                    state=line[10],
                                    post_code=line[11])
            new_address.save()
            address_join = PersonAddressJoin(person=new_person,
                                             address=new_address)
            address_join.save()

            new_phone = Phones(phone_number=line[12])
            new_phone.save()
            phone_join = PersonPhoneJoin(person=new_person,
                                         phone=new_phone)
            phone_join.save()

            new_email = Emails(email_address=line[13])
            new_email.save()
            email_join = PersonEmailJoin(person=new_person,
                                         email=new_email)
            email_join.save()

            new_case, case_created = Cases.objects.update_or_create(
                person=new_person,
                active=True,
                status=Statuses.objects.get(status_id=1)
            )

            if case_created:

                if new_test.result == TestResults.objects.get(result_id=1):
                    if new_test.test_type == TestTypes.objects.get(test_type_id=1):
                        if new_test.source != TestSources.objects.get(id=3):
                            new_case.confirmed = True
                            new_case.probable = False
                            new_case.monitor_not_case = False
                            new_case.save()
                        else:
                            new_case.confirmed = False
                            new_case.probable = True
                            new_case.monitor_not_case = False
                            new_case.save()
                    else:
                        new_case.confirmed = False
                        new_case.probable = True
                        new_case.monitor_not_case = False
                        new_case.save()

                case_test_join = CaseTestJoin(case=new_case,
                                              test=new_test)
                case_test_join.save()
                cases_added.append(new_case.case_id)
            else:
                messages.error(request, "Failed to create case for %s %s. Check the file entry and try again." % (new_person.first, new_person.last))
                email_join.delete()
                new_email.delete()
                phone_join.delete()
                new_phone.delete()
                address_join.delete()
                new_address.delete()
                new_person.delete()
                new_test.delete()
        else:
            messages.error(request, "%s %s already exists in the database." % (new_person.first, new_person.last))

    context = {}

    if len(cases_added) > 0:
        return redirect("case-upload-assign", case_list=cases_added)
    else:
        return render(request, template, context)


@login_required(login_url='/accounts/login/')
def case_upload_assign(request, case_list):

    cases = case_list[1:(len(case_list) - 1)]
    cases = cases.replace(" ", "")
    cases = cases.split(",")

    cases = Cases.objects.filter(case_id__in=cases)
    CaseAssignmentFormsest = formset_factory(AssignUploadedCaseForm, extra=len(cases))

    assignment = Assignments()

    users = AuthUser.objects.filter(id__gt=0)

    pending_status = AssignmentStatus.objects.get(status_id=1)

    if request.method == 'POST':
        # print('POST')

        caseassignments = CaseAssignmentFormsest(request.POST, prefix='case')

        assignform = NewAssignment(request.POST, instance=assignment)

        if caseassignments.is_valid() and assignform.is_valid():
            i = 0
            j = 0
            for caseassign in caseassignments:
                # print('in for')
                if caseassign.is_valid():
                    # print('valid form')
                    # print(caseassign.cleaned_data)
                    if caseassign.cleaned_data['assign_box']:
                        # print('checked box')
                        user_assigned = caseassign.cleaned_data['assign_box']
                        if user_assigned is not None and user_assigned != AuthUser.objects.get(id=1):
                            this_assign = Assignments(user=user_assigned,
                                                      case=cases[i],
                                                      status=pending_status,
                                                      assign_type=AssignmentType.objects.get(assign_type_id=1))
                            this_assign.save()
                i = i + 1

            return redirect('assignments')
        # print(caseassignments.errors)

    else:

        caseassignments = CaseAssignmentFormsest(prefix='case')

    return render(request, 'bulk-assign/multiple-assign.html', {'assigncases': zip(caseassignments, cases),
                                                                # 'assignform': assignform,
                                                                'assignformset': caseassignments,
                                                                })


@login_required(login_url='/accounts/login/')
def statistics_dashboard(request):

    # Collect starting info
    # Get all objects that have a valid status
    valid_status_list = list(range(1, 14))
    valid_status_list.append(17)
    print(f'Valid status ids: {valid_status_list}')

    qs = Cases.objects.filter(status_id__in=valid_status_list, monitor_not_case=0)
    confirmed_cases = qs.filter(confirmed=1)
    probable_cases = qs.filter(probable=1)
    deceased_cases = qs.filter(status_id=5) #COVID only deaths are this status
    deceased_probable = deceased_cases.filter(probable=1).count()
    deceased_confirmed = deceased_cases.filter(confirmed=1).count()
    released_cases = qs.filter(status_id__in=range(11, 14)) #covers ids 11-13
    current_hosp = qs.filter(status_id=4)

    # == CONFIRMED POSITIVE CASES ==
    print(f'Total valid cases: {len(qs)}')

    # Only select PCR tests with positive results that aren't self reported
    molecular_pos_tests = Tests.objects.filter(test_type_id=1, result_id=1, source_id__in=range(1, 3)) #covers ids 1-2
    print(f'Positive, official, PCR tests: {len(molecular_pos_tests)}')

    # Select the cases that are associated with the positive tests
    cases_with_mol_pos = CaseTestJoin.objects.filter(test_id__in=molecular_pos_tests.values('test_id'))
    print(f'Number cases associated with these tests: {len(cases_with_mol_pos)}')

    print('Building rcvd_chart')
    rcvd_chart = charts.prep_rcvd_data(qs, molecular_pos_tests, cases_with_mol_pos, 'confirmed')
    print('Finished getting rcvd_chart')

    rcvd_chart_by_sex = charts.prep_data_by_var(qs, molecular_pos_tests, cases_with_mol_pos, 'confirmed', 'sex')

    # # == NONCONFIRMED POSITIVE CASES ==
    #
    # # Only select Non-confirmatory tests with positive results that aren't self reported
    # noncomfirm_pos_tests = Tests.objects.filter(test_type_id__in=range(2, 4), result_id=1, source_id__in=range(1, 3))  # covers ids 1-2
    # print(f'Positive, official, Non-confirmatory tests: {len(molecular_pos_tests)}')
    #
    # # Select the cases that are associated with the positive tests
    # cases_with_nonconfirm_pos = CaseTestJoin.objects.filter(test_id__in=noncomfirm_pos_tests.values('test_id'))
    # print(f'Number cases associated with these tests: {len(cases_with_mol_pos)}')
    #
    # print('Building probable chart')
    # probable_chart = charts.prep_rcvd_data(qs, noncomfirm_pos_tests, cases_with_nonconfirm_pos, 'probable')
    # print('Finished getting probable chart')

    # == COUNTS ==
    deceased_count = deceased_cases.count()
    confirmed_case_count = confirmed_cases.count()
    probable_case_count = probable_cases.count()
    case_count = qs.count()
    released_count = released_cases.count()
    current_hosp_count = current_hosp.count()

    return render(request, 'statistics/statistics.html', {'rcvd_chart': rcvd_chart,
                                                          # 'probable_chart': probable_chart,
                                                          # 'deceased_count': deceased_count,
                                                          'deceased_confirmed': deceased_confirmed,
                                                          'deceased_probable': deceased_probable,
                                                          'case_count': case_count,
                                                          'confirmed_case_count': confirmed_case_count,
                                                          'probable_case_count': probable_case_count,
                                                          'released_count': released_count,
                                                          'current_hosp_count': current_hosp_count,
                                                          })


@login_required(login_url='/accounts/login/')
def edit_log(request, page, ctype, case_id, log_id):

    log = get_object_or_404(TraceLogs, log_id=log_id)

    if log.user_id == request.user.id:
        pass
    elif request.user.groups.filter(name='admin_user').exists():
        pass
    else:
        return render(request, 'error/permission.html')

    current_text = log.notes
    current_user = AuthUser.objects.get(id=request.user.id)

    if request.method == 'POST':

        editform = LogEditForm(request.POST,
                               initial={'previous_text': current_text,
                                        },
                               page=page,
                               ctype=ctype,
                               pid=case_id)
        # editform.log = log
        # editform.user_id = current_user
        # editform.edit_date = datetime.datetime.today()

        if editform.is_valid():
            log.notes = editform.cleaned_data['previous_text']

            this_edit = editform.save(commit=False)
            this_edit.previous_text = current_text
            this_edit.user = current_user
            this_edit.edit_date = datetime.datetime.today()
            this_edit.log = log
            this_edit.save()
            log.save()

            return redirect(page, cttype=ctype, pid=case_id)
        print(editform.errors)

    else:
        editform = LogEditForm(initial={'previous_text': current_text},
                               page=page,
                               ctype=ctype,
                               pid=case_id
                               )

    return render(request, 'edit/edit-log.html', {'editform': editform,
                                                  })
