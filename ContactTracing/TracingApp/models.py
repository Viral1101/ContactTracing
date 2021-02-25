# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Addresses(models.Model):
    address_id = models.AutoField(primary_key=True)
    street = models.TextField(blank=True, null=True)
    street2 = models.TextField(blank=True, null=True)
    city = models.TextField(blank=True, null=True)
    state = models.CharField(max_length=2, blank=True, null=True)
    post_code = models.CharField(max_length=5, blank=True, null=True)
    # people = models.ManyToManyField('Addresses', through='PersonAddressJoin')

    class Meta:
        # managed = False
        db_table = 'addresses'

    def __str__(self):
        if self.street:
            _street = self.street
        else:
            _street = ''
        if self.street2:
            _street2 = ' ' + self.street2
        else:
            _street2 = ''
        if self.street:
            _city = ' ' + self.city
        else:
            _city = self.city
        _state = self.state
        if self.post_code:
            _zip = self.post_code
        else:
            _zip = ''
        data = {'street': _street,
                'street2': _street2,
                'city': _city,
                'state': _state,
                'zip': _zip,
                }
        output = '{street}{street2}{city}, {state} {zip}'.format(**data)
        return output


class AssignmentType(models.Model):
    assign_type_id = models.AutoField(primary_key=True)
    assign_type = models.TextField()

    class Meta:
        managed = False
        db_table = 'assignment_type'

    def __str__(self):
        return self.assign_type


class Assignments(models.Model):
    join_id = models.AutoField(primary_key=True)
    case = models.ForeignKey('Cases', models.DO_NOTHING, blank=True, null=True)
    contact = models.ForeignKey('Contacts', models.DO_NOTHING, blank=True, null=True)
    outbreak = models.ForeignKey('Outbreaks', models.DO_NOTHING, blank=True, null=True)
    assign_type = models.ForeignKey(AssignmentType, models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey('AuthUser', models.DO_NOTHING, blank=True, null=True)
    status = models.ForeignKey('AssignmentStatus', models.DO_NOTHING)
    date_done = models.DateField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'assignments'

    def __str__(self):
        case = self.case
        contact = self.contact
        outbreak = self.outbreak
        target = ''
        if case is not None:
            target = case
        elif contact is not None:
            target = contact
        elif outbreak is not None:
            target = outbreak
        data = {'target': target,
                'user': self.user,
                'status': self.status}
        output = '{target}, {user}, {status}'.format(**data)
        return output


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'

    def __str__(self):
        return self.first_name + ' ' + self.last_name


class AuthUserGroups(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class CaseContactJoin(models.Model):
    join_id = models.AutoField(primary_key=True)
    case = models.ForeignKey('Cases', models.DO_NOTHING)
    contact = models.ForeignKey('Contacts', models.DO_NOTHING)
    relation_to_case = models.TextField(blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'case_contact_join'


class CaseLogJoin(models.Model):
    join_id = models.AutoField(primary_key=True)
    case = models.ForeignKey('Cases', models.DO_NOTHING)
    log = models.ForeignKey('TraceLogs', models.DO_NOTHING)

    class Meta:
        # managed = False
        db_table = 'case_log_join'


class CaseSxJoin(models.Model):
    join_id = models.AutoField(primary_key=True)
    case = models.ForeignKey('Cases', models.DO_NOTHING)
    sx = models.ForeignKey('SxLog', models.DO_NOTHING)

    class Meta:
        # managed = False
        db_table = 'case_sx_join'

    def __str__(self):
        data = {'case': self.case,
                'sx': self.sx}
        output = '{case} || {sx}'.format(**data)
        return output


class Cases(models.Model):
    case_id = models.AutoField(primary_key=True)
    person = models.ForeignKey('Persons', models.DO_NOTHING)
    test = models.ForeignKey('Tests', models.DO_NOTHING)
    confirmed = models.BooleanField(default=False, null=True)
    status = models.ForeignKey('Statuses', models.DO_NOTHING)
    tent_release = models.DateField(blank=True, null=True)
    iso_pcp = models.BooleanField(blank=True, null=True)
    reqs_pcp = models.TextField(blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)
    last_follow = models.DateField(blank=True, null=True)
    rel_pcp = models.BooleanField(blank=True, null=True)
    active = models.BooleanField()
    released = models.ForeignKey(AuthUser, models.DO_NOTHING, blank=True, null=True)
    old_case_no = models.TextField(blank=True, null=True)
    probable = models.BooleanField(default=False)
    able_to_isolate = models.ForeignKey('BooleanTable', models.DO_NOTHING, blank=True, null=True)
    text_follow_up = models.BooleanField(blank=True, null=True)
    email_follow_up = models.BooleanField(blank=True, null=True)
    monitor_not_case = models.BooleanField(default=False)
    hospitalized = models.BooleanField(default=False)
    icu = models.BooleanField(default=False)
    onset_date = models.DateField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'cases'

    def __str__(self):
        data = {'id': self.case_id,
                'person': self.person}
        output = 'C{id}: {person}'.format(**data)
        return output


class ContactLogJoin(models.Model):
    join_id = models.AutoField(primary_key=True)
    contact = models.ForeignKey('Contacts', models.DO_NOTHING)
    log = models.ForeignKey('TraceLogs', models.DO_NOTHING)

    class Meta:
        # managed = False
        db_table = 'contact_log_join'


class ContactPrefs(models.Model):
    pref_id = models.AutoField(primary_key=True)
    pref = models.TextField()

    class Meta:
        managed = False
        db_table = 'contact_prefs'

    def __str__(self):
        return self.pref


class ContactSxJoin(models.Model):
    join_id = models.AutoField(primary_key=True)
    case = models.ForeignKey('Contacts', models.DO_NOTHING)
    sx = models.ForeignKey('SxLog', models.DO_NOTHING)

    class Meta:
        # managed = False
        db_table = 'contact_sx_join'


class BooleanTable(models.Model):
    boolean_id = models.AutoField(primary_key=True)
    boolean = models.CharField(max_length=12)

    class Meta:
        managed = True
        db_table = 'boolean_table'

    def __str__(self):
        return self.boolean


class Contacts(models.Model):
    contact_id = models.AutoField(primary_key=True)
    person = models.ForeignKey('Persons', models.DO_NOTHING)
    init_exposure = models.DateField(blank=True, null=True)
    can_quarantine = models.BooleanField(blank=True, null=True)
    tent_qt_end = models.DateField(blank=True, null=True)
    status = models.ForeignKey('Statuses', models.DO_NOTHING)
    last_follow = models.DateField(blank=True, null=True)
    active = models.BooleanField()
    old_contact_no = models.TextField(blank=True, null=True)
    last_exposure = models.DateField(blank=True, null=True)
    able_to_quarantine = models.ForeignKey(BooleanTable, models.DO_NOTHING, blank=True, null=True)
    text_follow_up = models.BooleanField(blank=True, null=True)
    email_follow_up = models.BooleanField(blank=True, null=True)
    upgraded_case = models.ForeignKey(Cases, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'contacts'

    def __str__(self):
        data = {'id': self.contact_id,
                'person': self.person}
        output = 'CT{id}: {person}'.format(**data)
        return output


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class Emails(models.Model):
    email_id = models.AutoField(primary_key=True)
    email_address = models.CharField(max_length=320, blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'emails'

    def __str__(self):
        return "%s" % self.email_address


class Employers(models.Model):
    employer_id = models.AutoField(primary_key=True)
    employer_name = models.TextField(blank=True, null=True)
    phone = models.ForeignKey('Phones', models.DO_NOTHING, blank=True, null=True)
    email = models.ForeignKey(Emails, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'employers'


class ExternalCases(models.Model):
    ex_case_id = models.AutoField(primary_key=True)
    source = models.ForeignKey('ExternalSources', models.DO_NOTHING)
    rcvd_date = models.DateField(blank=True, null=True)
    active = models.IntegerField()

    class Meta:
        # managed = False
        db_table = 'external_cases'


class ExternalSources(models.Model):
    source_id = models.AutoField(primary_key=True)
    source_name = models.TextField()
    phone = models.ForeignKey('Phones', models.DO_NOTHING, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'external_sources'


class OutbreakCaseJoin(models.Model):
    join_id = models.AutoField(primary_key=True)
    case_id = models.IntegerField()
    outbreak_id = models.IntegerField()

    class Meta:
        # managed = False
        db_table = 'outbreak_case_join'


class OutbreakContactJoin(models.Model):
    join_id = models.AutoField(primary_key=True)
    outbreak_id = models.IntegerField()
    contact_id = models.IntegerField()

    class Meta:
        # managed = False
        db_table = 'outbreak_contact_join'


# class Outbreaks(models.Model):
#     outbreak_id = models.AutoField(primary_key=True)
#     address = models.ForeignKey(Addresses, models.DO_NOTHING, blank=True, null=True)
#     phone = models.ForeignKey('Phones', models.DO_NOTHING, blank=True, null=True)
#     active = models.IntegerField()
#
#     class Meta:
#         # managed = False
#         db_table = 'outbreaks'


class PersonEmailJoin(models.Model):
    join_id = models.AutoField(primary_key=True)
    person = models.ForeignKey('Persons', models.DO_NOTHING)
    email = models.ForeignKey(Emails, models.DO_NOTHING)

    class Meta:
        # managed = False
        db_table = 'person_email_join'

    def __str__(self):
        return "%s: %s" % (self.person, self.email)


class PersonEmployerJoin(models.Model):
    join_id = models.AutoField(primary_key=True)
    person = models.ForeignKey('Persons', models.DO_NOTHING)
    employer = models.ForeignKey(Employers, models.DO_NOTHING)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'person_employer_join'


class PersonPhoneJoin(models.Model):
    join_id = models.AutoField(primary_key=True)
    phone = models.ForeignKey('Phones', models.DO_NOTHING)
    person = models.ForeignKey('Persons', models.DO_NOTHING)
    note = models.TextField(blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'person_phone_join'

    def __str__(self):
        return "%s: %s" % (self.person, self.phone)


class Phones(models.Model):
    phone_id = models.AutoField(primary_key=True)
    phone_number = models.CharField(max_length=31)

    class Meta:
        # managed = False
        db_table = 'phones'

    def __str__(self):
        return "%s" % self.phone_number


class Persons(models.Model):
    person_id = models.AutoField(primary_key=True)
    first = models.TextField()
    last = models.TextField()
    mi = models.CharField(max_length=5, blank=True, null=True)
    suffix = models.CharField(max_length=10, blank=True, null=True)
    # address = models.ForeignKey(PersonAddressJoin, models.DO_NOTHING, blank=True, null=True)
    addys = models.ManyToManyField('Addresses', through='PersonAddressJoin')
    phones = models.ManyToManyField(Phones, through='PersonPhoneJoin')
    sex = models.CharField(max_length=1, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    pronunciation = models.TextField(blank=True, null=True)
    contact_pref = models.ForeignKey(ContactPrefs, models.DO_NOTHING, blank=True, null=True)
    needs_docs = models.IntegerField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    vacc_dose1 = models.DateField(blank=True, null=True)
    vacc_dose2 = models.DateField(blank=True, null=True)
    vacc_type1 = models.ForeignKey('VaccineTypes', models.DO_NOTHING, blank=True, null=True, related_name='type1')
    vacc_type2 = models.ForeignKey('VaccineTypes', models.DO_NOTHING, blank=True, null=True, related_name='type2')
    vacc_lot1 = models.TextField(blank=True, null=True)
    vacc_lot2 = models.TextField(blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'persons'

    def __str__(self):

        if self.sex is None:
            sex = "Unknown"
        elif self.sex == 'F' or self.sex == '0':
            sex = "Female"
        else:
            sex = "Male"

        data = {'first': self.first,
                'mi': '' if self.mi is None else (self.mi + ' '),
                'last': self.last,
                'suffix': '' if self.suffix is None or self.suffix == '' else (' ' + self.suffix),
                'dob': self.dob,
                'age': self.age,
                'sex': sex}
        output = '[{first} {mi}{last}{suffix}] DOB: {dob}, Age: {age}, Sex: {sex}'.format(**data)
        return output


class VaccineTypes(models.Model):
    vaccine_id = models.AutoField(primary_key=True)
    detail = models.TextField()

    class Meta:
        managed = True
        db_table = 'vaccine_types'
        ordering = ('detail',)

    def __str__(self):
        return self.detail


class PersonAddressJoin(models.Model):
    join_id = models.AutoField(primary_key=True)
    person = models.ForeignKey(Persons, models.DO_NOTHING, blank=True, null=True, related_name='people')
    address = models.ForeignKey(Addresses, models.DO_NOTHING, blank=True, null=True, related_name='addys')
    # address = models.ManyToManyField(Persons, through="self")

    class Meta:
        # managed = False
        db_table = 'person_address_join'

    def __str__(self):
        return "%s: %s" % (self.person, self.address)


class Roles(models.Model):
    role_id = models.AutoField(primary_key=True)
    role = models.TextField()

    class Meta:
        managed = False
        db_table = 'roles'


class Statuses(models.Model):
    status_id = models.AutoField(primary_key=True)
    status = models.TextField()

    class Meta:
        managed = False
        db_table = 'statuses'

    def __str__(self):
        return self.status


class SxStates(models.Model):
    state_id = models.AutoField(primary_key=True)
    sx_state = models.TextField()

    class Meta:
        managed = False
        db_table = 'sx_states'

    def __str__(self):
        return self.sx_state


class SymptomDefs(models.Model):
    symptom_id = models.AutoField(primary_key=True)
    symptom = models.TextField(blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'symptom_defs'

    def __str__(self):
        return self.symptom


class SxLog(models.Model):
    log_id = models.AutoField(primary_key=True)
    start = models.DateField(blank=True, null=True)
    end = models.DateField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    alt_dx = models.TextField(blank=True, null=True)
    sx_state = models.ForeignKey(SxStates, models.DO_NOTHING)
    rec_date = models.DateField(blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    symptom = models.ForeignKey(SymptomDefs, models.DO_NOTHING)

    class Meta:
        # managed = False
        db_table = 'sx_log'

    def __str__(self):
        data = {'start': self.start,
                'end': self.end,
                'alternate':  'alternate dx: ' + self.alt_dx,
                'note': 'notes:' + self.note,
                'state': self.sx_state.sx_state}
        output = 'Started: {start} // Ended: {end} // {alternate} // {note} // {state}'.format(**data)
        return output


class SxLogJoin(models.Model):
    join_id = models.AutoField(primary_key=True)
    sx = models.ForeignKey('Symptoms', models.DO_NOTHING)
    sx_log = models.ForeignKey('SxLog', models.DO_NOTHING)

    class Meta:
        # managed = False
        db_table = 'sx_log_join'

    def __str__(self):
        data = {'symptom': self.sx,
                'log': self.sx_log}
        output = '{symptom} {log}'.format(**data)
        return output


class Symptoms(models.Model):
    sx_id = models.AutoField(primary_key=True)
    symptom = models.ForeignKey(SymptomDefs, models.DO_NOTHING)

    class Meta:
        # managed = False
        db_table = 'symptoms'

    def __str__(self):
        data = {'symptom': self.symptom,
                'id': self.sx_id}
        output = 'SX#: {id} - {symptom}'.format(**data)
        return output


class TestTypes(models.Model):
    test_type_id = models.AutoField(primary_key=True)
    test_type = models.TextField()

    class Meta:
        managed = False
        db_table = 'test_types'

    def __str__(self):
        return self.test_type


class Tests(models.Model):
    test_id = models.AutoField(primary_key=True)
    test_trace = models.TextField(blank=True, null=True)
    sample_date = models.DateField(blank=True, null=True)
    result_date = models.DateField(blank=True, null=True)
    rcvd_date = models.DateField(blank=True, null=True)
    result = models.ForeignKey('TestResults', models.DO_NOTHING, blank=True, null=True)
    test_type = models.ForeignKey(TestTypes, models.DO_NOTHING, blank=True, null=True)
    logged_date = models.DateField(blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING, blank=True, null=True)
    source = models.ForeignKey('TestSources', models.DO_NOTHING, null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'tests'


class TraceLogs(models.Model):
    log_id = models.AutoField(primary_key=True)
    notes = models.TextField()
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    log_date = models.DateField()

    class Meta:
        # managed = False
        db_table = 'trace_logs'

    def __str__(self):
        text = self.notes[:30]
        first = self.user.first_name
        last = self.user.last_name
        log_date = self.log_date

        data = {'f': first,
                'l': last,
                't': text,
                'log': log_date}
        output = '{t} [[{f} {l} {log}]]'.format(**data)

        return output


class Users(models.Model):
    user_id = models.AutoField(primary_key=True)
    first = models.TextField()
    last = models.TextField()
    initials = models.CharField(max_length=3)
    email_id = models.IntegerField()
    role_id = models.IntegerField()
    pass_field = models.CharField(db_column='pass',
                                  max_length=255)  # Field renamed because it was a Python reserved word.
    active = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'users'


class Clusters(models.Model):
    cluster_id = models.AutoField(primary_key=True)
    # details = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'clusters'


class ClusterCaseJoin(models.Model):
    join_id = models.AutoField(primary_key=True)
    cluster = models.ForeignKey(Clusters, models.DO_NOTHING)
    case = models.ForeignKey(Cases, models.DO_NOTHING, related_name='developed')
    index_case = models.ForeignKey(Cases, models.DO_NOTHING, null=True, blank=True, related_name='exposing')
    associated_contact = models.ForeignKey(Contacts, models.DO_NOTHING, null=True, related_name='associated_contact')
    last_exposed = models.DateField(null=True, blank=True)
    details = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'cluster_case_join'


class CaseLinks(models.Model):
    link_id = models.AutoField(primary_key=True)
    exposing_case = models.ForeignKey(Cases, models.DO_NOTHING, related_name='exposing_old')
    developed_case = models.ForeignKey(Cases, models.DO_NOTHING, related_name='developed_old')
    developed_contact = models.ForeignKey(Contacts, models.DO_NOTHING)

    class Meta:
        managed = True
        db_table = 'case_links'


class HouseHolds(models.Model):
    household_id = models.AutoField(primary_key=True)

    class Meta:
        managed = True
        db_table = 'households'


class HHPersonJoin(models.Model):
    join_id = models.AutoField(primary_key=True)
    household = models.ForeignKey(HouseHolds, models.DO_NOTHING)
    person = models.ForeignKey(Persons, models.DO_NOTHING)

    class Meta:
        managed = True
        db_table = 'hh_person_join'


class CaseTestJoin(models.Model):
    join_id = models.AutoField(primary_key=True)
    case = models.ForeignKey(Cases, models.DO_NOTHING)
    test = models.ForeignKey(Tests, models.DO_NOTHING)

    class Meta:
        managed = True
        db_table = 'case_test_join'


class ContactTestJoin(models.Model):
    join_id = models.AutoField(primary_key=True)
    contact = models.ForeignKey(Contacts, models.DO_NOTHING)
    test = models.ForeignKey(Tests, models.DO_NOTHING)

    class Meta:
        managed = True
        db_table = 'contact_test_join'


class TestSources(models.Model):
    source = models.CharField(max_length=42, default='Unknown')

    class Meta:
        managed = True
        db_table = 'test_sources'

    def __str__(self):
        return self.source


class TestResults(models.Model):
    result_id = models.AutoField(primary_key=True)
    result = models.CharField(max_length=15)

    class Meta:
        managed = True
        db_table = 'test_results'

    def __str__(self):
        return self.result


class AssignmentStatus(models.Model):
    status_id = models.AutoField(primary_key=True)
    status = models.CharField(max_length=15)

    class Meta:
        managed = True
        db_table = 'assignment_statuses'

    def __str__(self):
        return self.status


class Locations(models.Model):
    location_id = models.AutoField(primary_key=True)
    address = models.ForeignKey(Addresses, models.DO_NOTHING, null=True, blank=True)
    name = models.CharField(max_length=256)

    class Meta:
        managed = True
        db_table = 'locations'

    def __str__(self):
        data = {'name': self.name,
                'address': self.address}
        output = '{name}: {address}'.format(**data)
        return output


class LocationPhoneJoin(models.Model):
    join_id = models.AutoField(primary_key=True)
    location = models.ForeignKey(Locations, models.DO_NOTHING)
    phone = models.ForeignKey(Phones, models.DO_NOTHING)

    class Meta:
        managed = True
        db_table = 'location_phone_join'

    def __str__(self):
        return self.phone


class Outbreaks(models.Model):
    outbreak_id = models.AutoField(primary_key=True)
    date_of_exposure = models.DateField(blank=True, null=True)
    location = models.ForeignKey(Locations, models.DO_NOTHING)
    active = models.BooleanField()

    class Meta:
        managed = True
        db_table = 'outbreaks'

    def __str__(self):
        data = {'location': self.location,
                'date': self.date_of_exposure}
        output = '{location} Outbreak on:{date}'.format(**data)
        return output


class OutbreakManagerJoin(models.Model):
    join_id = models.AutoField(primary_key=True)
    outbreak = models.ForeignKey(Outbreaks, models.DO_NOTHING)
    person = models.ForeignKey(Persons, models.DO_NOTHING)
    position = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'outbreak_manager_join'


class OutbreakClusterJoin(models.Model):
    join_id = models.AutoField(primary_key=True)
    outbreak = models.ForeignKey(Outbreaks, models.DO_NOTHING)
    cluster = models.ForeignKey(Clusters, models.DO_NOTHING)

    class Meta:
        managed = True
        db_table = 'outbreak_cluster_join'


class Exposures(models.Model):
    exposure_id = models.AutoField(primary_key=True)
    initial_exposure = models.DateField(blank=True, null=True)
    last_exposure = models.DateField(blank=True, null=True)
    quarantine_end = models.DateField(blank=True, null=True)
    relation_to_case = models.TextField(blank=True, null=True)
    location = models.ForeignKey(Locations, models.DO_NOTHING, null=True)
    outbreak = models.ForeignKey(Outbreaks, models.DO_NOTHING, null=True)
    exposing_case = models.ForeignKey(Cases, models.DO_NOTHING, null=True)
    contact = models.ForeignKey(Contacts, models.DO_NOTHING, null=True)

    class Meta:
        managed = True
        db_table = 'exposures'


class ContactExposureJoin(models.Model):
    join_id = models.AutoField(primary_key=True)
    contact = models.ForeignKey(Contacts, models.DO_NOTHING, null=False)
    exposure = models.ForeignKey(Exposures, models.DO_NOTHING, null=False)

    class Meta:
        managed = True
        db_table = 'contact_exposure_join'


class EpitraxPCHDCaseJoin(models.Model):
    join_id = models.AutoField(primary_key=True)
    person = models.ForeignKey(Persons, models.DO_NOTHING)
    case = models.ForeignKey(Cases, models.DO_NOTHING, null=True)
    contact = models.ForeignKey(Contacts, models.DO_NOTHING, null=True)
    epi_person_id = models.BigIntegerField()
    cmr = models.BigIntegerField(null=True)

    class Meta:
        managed = True
        db_table = 'epitrax_pchd_case_join'


class LogEdits(models.Model):
    edit_id = models.AutoField(primary_key=True)
    log = models.ForeignKey(TraceLogs, models.DO_NOTHING, null=False)
    previous_text = models.TextField(null=False, blank=False)
    edit_reason = models.TextField(null=False, blank=False)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING, null=False)
    edit_date = models.DateField(null=False, blank=False)

    class Meta:
        managed = True
        db_table = 'log_edits'