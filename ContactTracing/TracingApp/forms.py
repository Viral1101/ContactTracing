from django import forms
from django_localflavor_us.forms import USStateSelect, USZipCodeField, USPhoneNumberField
from .models import *
from bootstrap_datepicker_plus import DatePickerInput
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from dateutil.relativedelta import relativedelta
import datetime
import re
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div


class NewPhoneNumberForm(forms.ModelForm):

    class Meta:
        model = Phones
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        phone = cleaned_data.get('phone_number')

        phone_exists = Phones.objects.filter(phone_number=phone)
        if phone_exists:
            min_id = phone_exists[0].phone_id
            for phon in phone_exists:
                min_id = min(min_id, phon.phone_id)
            self.cleaned_data['phone_id'] = min_id
            print(self.cleaned_data['phone_id'])


class NewAddressForm(forms.ModelForm):

    # Address data
    street = forms.CharField(required=False)
    street2 = forms.CharField(required=False)
    city = forms.CharField(required=False)
    state = forms.CharField(widget=USStateSelect, initial='MO', required=False)
    post_code = forms.CharField(max_length=5, min_length=5, required=False)

    def clean_post_code(self):
        data = self.cleaned_data['post_code']

        if not re.search('\d{5}$', data):
            raise ValidationError(_('Invalid zip - Zip should be in the form #####'))

        return data

    def clean(self):
        cleaned_data = super().clean()
        street = cleaned_data.get('street')
        street2 = cleaned_data.get('street2')
        city = cleaned_data.get('city')
        state = cleaned_data.get('state')
        post_code = cleaned_data.get('post_code')

        street_exists = Addresses.objects.filter(street=street)
        if street_exists:
            street2_exists = street_exists.filter(street2=street2)
            if street2_exists:
                city_exists = street2_exists.filter(city=city)
                if city_exists:
                    state_exists = city_exists.filter(state=state)
                    if state_exists:
                        zip_exists = state_exists.filter(post_code=post_code)
                        if zip_exists:
                            min_id = zip_exists[0].address_id
                            for zip_c in zip_exists:
                                min_id = min(min_id, zip_c.address_id)
                            # msg = "Address exists. Check to ensure no typos."
                            # self.add_error('street', msg)
                            self.cleaned_data['address_id'] = min_id
                            print(self.cleaned_data['address_id'])
        return cleaned_data

    class Meta:
        model = Addresses
        # fields = '__all__'
        fields = ['street',
                  'street2',
                  'city',
                  'state',
                  'post_code',
                  ]


class NewPersonForm2(forms.ModelForm):

    class Meta:
        model = PersonAddressJoin
        fields = '__all__'


class CaseInvestigation(forms.ModelForm):

    class Meta:
        model = Cases
        fields = '__all__'


class PersonForm(forms.ModelForm):

    class Meta:
        model = Persons
        fields = '__all__'


class NewPersonForm(forms.ModelForm):
    # Basic Person Data
    first = forms.CharField()
    mi = forms.CharField(max_length=2, required=False)
    last = forms.CharField()

    suff_options = [('', '---'),
                    ('Jr', "Jr"),
                    ('Sr', "Sr"),
                    ('III', "III"),
                    ('IV', "IV")]

    suffix = forms.TypedChoiceField(choices=suff_options, coerce=str, required=False)

    sexes = [('', '------'),
             ('F', "Female"),
             ('M', "Male")]

    sex = forms.TypedChoiceField(choices=sexes, coerce=str)
    dob = forms.DateField(widget=DatePickerInput(), required=False)

    def clean_dob(self):
        data = self.cleaned_data['dob']

        #     Date should only exist in the past
        if data >= datetime.date.today():
            print('dob error')
            raise ValidationError(_('Invalid date - Date should be in the past'))

        return data

    def clean_age(self):
        data = self.cleaned_data['age']

        if not data:
            data = relativedelta(datetime.date.today(), self.cleaned_data['dob']).years

        return data

    def clean(self):
        print("in clean")
        cleaned_data = super().clean()
        first = cleaned_data.get('first')
        last = cleaned_data.get('last')
        dob = cleaned_data.get('dob')
        print(first)
        print(last)
        print(dob)

        last_exists = Persons.objects.filter(last=last)
        if last_exists:
            print("last exists")
            first_exists = last_exists.filter(first=first)
            if first_exists:
                print('first exists')
                dob_exists = first_exists.filter(dob=dob)
                if dob_exists:
                    print('dob exists')
                    msg = "Person already exists. Check First name, Last name, and Date of Birth. " \
                          "Convert existing contact?"
                    self.add_error('first', msg)
        print("end clean")
        return cleaned_data

    class Meta:
        model = Persons
        fields = ['first',
                  'mi',
                  'last',
                  'suffix',
                  'sex',
                  'dob',
                  'age',
                  ]


class CaseForm(forms.ModelForm):
    active = forms.BooleanField()
    confirmed = forms.BooleanField()
    # last_follow = forms.DateField(widget=DatePickerInput())
    # release_date = forms.DateField(widget=DatePickerInput())
    # rel_pcp = forms.BooleanField()
    # iso_pcp = forms.BooleanField()
    # tent_release = forms.DateField(widget=DatePickerInput())

    class Meta:
        model = Cases
        exclude = ['test',
                   'person',
                   'old_case_no',
                   'last_follow',
                   'release_date',
                   'tent_release',
                   ]


class TraceLogForm(forms.ModelForm):

    class Meta:
        model = TraceLogs
        fields = ['notes',
                  ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.layout = Layout(
            Column('notes', css_class='form-group col-md-4 mb-0'))


class PersonFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.layout = Layout(
            Row(
                Column('first', css_class='form-group col-md-4 mb-0'),
                Column('mi', css_class='form-group col-md-2 mb-0'),
                Column('last', css_class='form-group col-md-4 mb-0'),
                Column('suffix', css_class='form-group col-md-2 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('sex', css_class='form-group col-md-2 mb-0'),
                Column('dob', css_class='form-group col-md-4 mb-0'),
                Column('age', css_class='form-group col-md-2 mb-0'),
                css_class='form-row'
            ),
        )


class ContactFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.layout = Layout(
            Row(
                Column('init_exposure', css_class='form-group col-md-4 mb-0'),
                Column('last_exposure', css_class='form-group col-md-4 mb-0'),
                Column('ten_qt_end', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('can_quarantine', css_class='form-group col-md-4 mb-0'),
                Column('status', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('mark_as_contacted', css_class='form-group col-md-5 mb-0'),
                Column('copy_case_notes', css_class='form-group col-md-5 mb-0')
            )
        )


class SymptomLogSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.layout = Layout(
            Div(
                Div(
                    Column('symptom', css_class='form-group col-md-4 mb-0'),
                    css_class='card-header'
                ),
                Div(
                    Row(
                        Column('sx_state', css_class='form-group col-md-4 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('start', css_class='form-group col-md-6 mb-0'),
                        Column('end', css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('note', css_class='form-group col-md-6 mb-0'),
                        Column('alt_dx', css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ),
                    css_class='card-body'
                ),
                css_class='card'
            )
        )
        self.render_required_fields = True


class SymptomLogForm(forms.ModelForm):

    start = forms.DateField(widget=DatePickerInput(), required=False)
    end = forms.DateField(widget=DatePickerInput(), required=False)

    class Meta:
        model = SxLog
        fields = ['symptom',
                  'sx_state',
                  'start',
                  'end',
                  'note',
                  'alt_dx',
                  ]

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Column('symptom', css_class='form-group col-md-4 mb-0'),
                    css_class='card-header'
                ),
                Div(
                    Row(
                        Column('sx_state', css_class='form-group col-md-4 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('start', css_class='form-group col-md-6 mb-0'),
                        Column('end', css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('note', css_class='form-group col-md-6 mb-0'),
                        Column('alt_dx', css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ),
                    css_class='card-body'
                ),
                css_class='card'
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['rec_date'] = datetime.date.today()
        return cleaned_data


class SymptomForm(forms.ModelForm):

    class Meta:
        model = Symptoms
        fields = '__all__'


class NewAssignment(forms.ModelForm):
    class Meta:
        model = Assignments
        fields = ['user',
                  'assign_type',
                  'status',
                  ]


class AddContactAddress(forms.ModelForm):

    use_case_address = forms.BooleanField(required=False)
    street = forms.CharField(required=False)
    street2 = forms.CharField(required=False)
    city = forms.CharField(required=False)
    state = forms.CharField(widget=USStateSelect, initial='MO', required=False)
    post_code = forms.CharField(max_length=5, min_length=5, required=False)

    class Meta:
        model = Addresses
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.layout = Layout(
            Row(
                Column('use_case_address', css_class='form-group col-md-5 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('street', css_class='form-group col-md-5 mb-0'),
                Column('street2', css_class='form-group col-md-5 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('city', css_class='form-group col-md-4 mb-0'),
                Column('state', css_class='form-group col-md-3 mb-0'),
                Column('post_code', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            )
        )

    def clean_post_code(self):
        data = self.cleaned_data['post_code']

        if not re.search('\d{5}$', data):
            raise ValidationError(_('Invalid zip - Zip should be in the form #####'))

        return data

    def clean(self):
        cleaned_data = super().clean()
        street = cleaned_data.get('street')
        street2 = cleaned_data.get('street2')
        city = cleaned_data.get('city')
        state = cleaned_data.get('state')
        post_code = cleaned_data.get('post_code')

        street_exists = Addresses.objects.filter(street=street)
        if street_exists:
            street2_exists = street_exists.filter(street2=street2)
            if street2_exists:
                city_exists = street2_exists.filter(city=city)
                if city_exists:
                    state_exists = city_exists.filter(state=state)
                    if state_exists:
                        zip_exists = state_exists.filter(post_code=post_code)
                        if zip_exists:
                            min_id = zip_exists[0].address_id
                            for zip_c in zip_exists:
                                min_id = min(min_id, zip_c.address_id)
                            # msg = "Address exists. Check to ensure no typos."
                            # self.add_error('street', msg)
                            self.cleaned_data['address_id'] = min_id
                            print(self.cleaned_data['address_id'])
        return cleaned_data


class AddContactAddressHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.layout = Layout(
            Row(
                Column('use_case_address', css_class='form-group col-md-5 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('street', css_class='form-group col-md-5 mb-0'),
                Column('street2', css_class='form-group col-md-5 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('city', css_class='form-group col-md-4 mb-0'),
                Column('state', css_class='form-group col-md-3 mb-0'),
                Column('post_code', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            )
        )


class AddContactPhone(forms.ModelForm):

    use_case_phone = forms.BooleanField(required=False)
    phone_number = forms.CharField(required=False)

    class Meta:
        model = Phones
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.layout = Layout(
            Row(
                Column('use_case_phone', css_class='form-group col-md-5 mb-0'),
                css_class='form-row'),
            Row(
                Column('phone_number', css_class='form-group col-md-5 mb-0'),
                css_class='form-row'
            )
        )


class AddContactPhoneHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.layout = Layout(
            Row(
                Column('use_case_phone', css_class='form-group col-md-5 mb-0'),
                css_class='form-row'),
            Row(
                Column('phone_number', css_class='form-group col-md-5 mb-0'),
                css_class='form-row'
            )
        )


class AddContactForm(forms.ModelForm):

    init_exposure = forms.DateField(widget=DatePickerInput(), required=False)
    last_exposure = forms.DateField(widget=DatePickerInput(), required=False)
    tent_qt_end = forms.DateField(widget=DatePickerInput(), required=False)

    can_qt_options = [('', 'Unknown'),
                      (True, 'Yes'),
                      (False, 'No'),
                      ]
    can_quarantine = forms.TypedChoiceField(choices=can_qt_options, required=False)

    mark_as_contacted = forms.BooleanField(required=False)
    copy_case_notes = forms.BooleanField(required=False)

    class Meta:
        model = Contacts
        exclude = ['person',
                   ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.layout = Layout(
            Row(
                Column('init_exposure', css_class='form-group col-md-4 mb-0'),
                Column('last_exposure', css_class='form-group col-md-4 mb-0'),
                Column('ten_qt_end', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('can_quarantine', css_class='form-group col-md-4 mb-0'),
                Column('status', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('mark_as_contacted', css_class='form-group col-md-5 mb-0'),
                Column('copy_case_notes', css_class='form-group col-md-5 mb-0'),
                css_class='form-row'
            )
        )


class NewTest(forms.ModelForm):

    sample_date = forms.DateField(widget=DatePickerInput(), required=False)
    result_date = forms.DateField(widget=DatePickerInput(), required=False)
    rcvd_date = forms.DateField(widget=DatePickerInput(), required=False)
    result = forms.BooleanField()
    logged_date = forms.DateField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Tests
        fields = '__all__'

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        # self.logged_date = datetime.date.today()

    def clean_status(self):
        return False

    def clean_logged_date(self):
        return datetime.date.today()

    # def clean(self):
        # self.logged_date = datetime.date.today()
        # super().clean()
