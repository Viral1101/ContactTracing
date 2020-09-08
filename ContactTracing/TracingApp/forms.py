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
from crispy_forms.layout import Layout, Submit, Row, Column, Div, Button


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


class AddressesForm(forms.ModelForm):
    address_id = forms.IntegerField(widget=forms.HiddenInput, required=False)
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

    class Meta:
        model = Addresses
        fields = ['street',
                  'street2',
                  'city',
                  'state',
                  'post_code',
                  'address_id',
                  ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.helper = FormHelper(self)
        self.fields['address_id'].disabled = True
        self.form_tag = False
        self.disable_csrf = True
        self.helper.layout = Layout(
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


class AddressesFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.form_tag = False
        self.disable_csrf = True
        self.layout = Layout(
            Div(
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
                ),
            )
        )
        self.render_required_fields = True
        # self.add_input(Button('add_address', "Add Address", css_class='btn-info'))


class PhoneForm(forms.ModelForm):
    phone_number = forms.CharField(required=False)

    class Meta:
        model = Phones
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            Div(
                Row(
                    Column('phone_number', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                )
            )
        )


class PhoneFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.form_tag = False
        self.disable_csrf = True
        self.layout = Layout(
            Div(
                Row(
                    Column('phone_number', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                )
            )
        )
        self.render_required_fields = True
        # self.add_input(Button('add_phone', "Add Phone", css_class='btn-info'))


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
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

    class Meta:
        model = Persons
        exclude = ['addys',
                   'phones',
                   ]


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

        try:
            if cleaned_data['pk']:
                return cleaned_data
        except KeyError:
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


class InvestigationCaseForm(forms.ModelForm):
    active = forms.BooleanField(required=False)
    confirmed = forms.BooleanField(required=False)
    # last_follow = forms.DateField(widget=DatePickerInput())
    # release_date = forms.DateField(widget=DatePickerInput())
    rel_pcp = forms.BooleanField(required=False)
    iso_pcp = forms.BooleanField(required=False)
    # tent_release = forms.DateField(widget=DatePickerInput())
    reqs_pcp = forms.CharField(required=False)
    # release_date = forms.DateField(widget=DatePickerInput)
    last_follow = forms.DateField(required=False, widget=forms.HiddenInput)
    rel_pcp = forms.BooleanField(required=False)

    class Meta:
            model = Cases
            exclude = ['test',
                       'person',
                       'old_case_no',
                       'release_date',
                       'tent_release',
                       ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rel_pcp'].label = 'Released by PCP'
        self.fields['iso_pcp'].label = 'Isolation Order by PCP'
        self.fields['reqs_pcp'].label = 'PCP requirements for release'
        self.fields['confirmed'].label = 'Positive Test Confirmation'
        self.fields['last_follow'].disabled = True
        # self.fields['tent_release'].label = 'Tentative Release Date'
        self.form_method = 'post'
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            Row(
                Column('confirmed', css_class='form-group col-md-2 mb-0'),
                Column('active', css_class='form-group col-md-2 mb-0'),
                Column('status', css_class='form-group col-md-4 mb-0'),
                # Column('old_case_no', css_class='form-group col-md-2 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('iso_pcp', css_class='form-group col-md-2 mb-0'),
                Column('reqs_pcp', css_class='form-group col-md-4 mb-0'),
                Column('rel_pcp', css_class='form-group col-md-2 mb-0'),
                # Column('tent_release', css_class='form-group col-md-2 mb-0'),
                css_class='form-row'
            )
        )

    def clean_status(self):
        data = self.cleaned_data['status']
        # print(data)
        # print(Statuses.objects.get(status_id=1))
        if data == Statuses.objects.get(status_id=1):
            raise ValidationError(_('Invalid case status - Case should not still need investigation'))
        return data

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data['status'] != 7:
            cleaned_data['last_follow'] = datetime.date.today()
        return cleaned_data


class CaseForm(forms.ModelForm):
    active = forms.BooleanField(required=False)
    confirmed = forms.BooleanField(required=False)
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            Column('confirmed', css_class='form-group col-md-3 mb-0'),
            Column('active', css_class='form-group col-md-3 mb-0'),
            Column('status', css_class='form-group col-md-6 mb-0')
        )

    def clean_status(self):
        data = self.cleaned_data['status']
        print(data)
        print(Statuses.objects.get(status_id=1))
        if data == Statuses.objects.get(status_id=1):
            raise ValidationError(_('Invalid case status - Case should not still need investigation'))
        return data


class ContactTraceLogForm(forms.ModelForm):
    notes = forms.CharField(widget=forms.Textarea(), required=False)
    log_date = forms.DateField(widget=forms.HiddenInput(), required=False)
    user = forms.ModelChoiceField(widget=forms.HiddenInput(), queryset=AuthUser.objects.none(), required=False)

    class Meta:
        model = TraceLogs
        fields = ['notes',
                  'user',
                  'log_date',
                  ]

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['user'].queryset = AuthUser.objects.filter(id=user.id)
        self.fields['user'].widget.attrs['readonly'] = True
        self.fields['log_date'].widget.attrs['readonly'] = True
        self.fields['user'].widget.attrs['disabled'] = True
        self.fields['log_date'].widget.attrs['disabled'] = True
        self.form_method = 'post'
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.layout = Layout(
            Row(
                Column('notes', css_class='form-group col-md-4 mb-0'),
                Column('user', css_class='form-group col-md-2 mb-0'),
                Column('log_date', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
        )

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['log_date'] = datetime.date.today()
        cleaned_data['user'] = AuthUser.objects.get(id=self.user.id)
        print(cleaned_data)
        return cleaned_data


class NewTraceLogForm(forms.ModelForm):
    notes = forms.CharField(widget=forms.Textarea(), required=False)
    log_date = forms.DateField(widget=forms.HiddenInput(), required=False)
    user = forms.ModelChoiceField(widget=forms.HiddenInput(), queryset=AuthUser.objects.none(), required=False)

    class Meta:
        model = TraceLogs
        fields = ['notes',
                  'user',
                  'log_date',
                  ]

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['user'].queryset = AuthUser.objects.filter(id=user.id)
        self.fields['user'].widget.attrs['readonly'] = True
        self.fields['log_date'].widget.attrs['readonly'] = True
        self.fields['user'].widget.attrs['disabled'] = True
        self.fields['log_date'].widget.attrs['disabled'] = True
        self.form_method = 'post'
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.layout = Layout(
            Row(
                Column('notes', css_class='form-group col-md-4 mb-0'),
                Column('user', css_class='form-group col-md-2 mb-0'),
                Column('log_date', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
        )

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['log_date'] = datetime.date.today()
        cleaned_data['user'] = self.user
        print(cleaned_data)
        return cleaned_data


class TraceLogForm(forms.ModelForm):
    notes = forms.CharField(required=False)
    log_date = forms.DateField(required=False)
    user = forms.ModelChoiceField(queryset=AuthUser.objects.all(), required=False)

    class Meta:
        model = TraceLogs
        fields = ['notes',
                  'user',
                  'log_date',
                  ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.user = user
        # self.fields['user'].queryset = AuthUser.objects.filter(id=user.id)
        self.fields['notes'].disabled = True
        self.fields['user'].widget.attrs['readonly'] = True
        self.fields['log_date'].widget.attrs['readonly'] = True
        self.fields['user'].widget.attrs['disabled'] = True
        self.fields['log_date'].widget.attrs['disabled'] = True
        self.form_method = 'post'
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.layout = Layout(
            Row(
                Column('notes', css_class='form-group col-md-4 mb-0'),
                Column('user', css_class='form-group col-md-2 mb-0'),
                Column('log_date', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
        )


class TraceLogFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.form_tag = False
        self.disable_csrf = True
        self.layout = Layout(
            Row(
                Column('user', css_class='form-group col-md-2 mb-0'),
                Column('log_date', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('notes', css_class='form-group mb-0'),
                css_class='form-row'
            ),
        )


class OldTraceLogFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.form_tag = False
        self.disable_csrf = True
        self.layout = Layout(
            Div(
                Div(
                    Row(
                        Column('user', css_class='col-md-2 mb-0'),
                        Column('log_date', css_class='col-md-2 mb-0'),
                        css_class='form-row'
                    ),
                    css_class='card-header'
                ),
                Div(
                    Column('notes', css_class='form-group mb-0'),
                    css_class='card-body'
                ),
                css_class='card'
            )
        )


class PersonFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.form_tag = False
        self.disable_csrf = True
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
        self.form_tag = False
        self.disable_csrf = True
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
        self.form_tag = False
        self.disable_csrf = True
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


class NewSymptomLogForm(forms.ModelForm):

    start = forms.DateField(widget=DatePickerInput(), required=False)
    end = forms.DateField(widget=DatePickerInput(), required=False)
    # rec_date = forms.DateField(widget=forms.HiddenInput())
    user = forms.ModelChoiceField(widget=forms.HiddenInput(), queryset=AuthUser.objects.none(), required=False)
    note = forms.CharField(required=False)
    alt_dx = forms.CharField(required=False)

    class Meta:
        model = SxLog
        fields = ['symptom',
                  'sx_state',
                  'start',
                  'end',
                  'note',
                  'alt_dx',
                  'rec_date',
                  'user',
                  ]

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['user'].queryset = AuthUser.objects.filter(id=user.id)
        # self.fields['user'].queryset = AuthUser.objects.filter(id=self.user)
        self.fields['user'].widget.attrs['readonly'] = True
        self.fields['rec_date'].widget.attrs['readonly'] = True
        self.fields['user'].widget.attrs['disabled'] = True
        self.fields['rec_date'].widget.attrs['disabled'] = True
        self.fields['alt_dx'].label = 'Alternate Diagnosis'
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
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
        self.helper.render_hidden_fields = False

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['rec_date'] = datetime.date.today()
        cleaned_data['user'] = self.user
        print(cleaned_data)
        return cleaned_data


class SymptomLogForm(forms.ModelForm):

    start = forms.DateField(widget=DatePickerInput(), required=False)
    end = forms.DateField(widget=DatePickerInput(), required=False)
    rec_date = forms.DateField(widget=forms.HiddenInput(), required=False)
    user = forms.ModelChoiceField(widget=forms.HiddenInput(), queryset=AuthUser.objects.none(), required=False)

    class Meta:
        model = SxLog
        fields = ['symptom',
                  'sx_state',
                  'start',
                  'end',
                  'note',
                  'alt_dx',
                  'rec_date',
                  'user',
                  ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.user = user
        # self.fields['user'].queryset = AuthUser.objects.filter(id=user.id)
        for nam, field in self.fields.items():
            field.disabled = True
        self.fields['alt_dx'].label = 'Alternate Diagnosis'
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
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
        self.helper.render_hidden_fields = False

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['rec_date'] = datetime.date.today()
        # cleaned_data['user'] = AuthUser.objects.get(id=self.user.id)
        return cleaned_data


class OldSymptomLogForm(forms.ModelForm):

    symptom = forms.ModelChoiceField(queryset=SymptomDefs.objects.all(), required=False)
    start = forms.DateField(widget=DatePickerInput(), required=False)
    end = forms.DateField(widget=DatePickerInput(), required=False)
    rec_date = forms.DateField(required=False)
    user = forms.ModelChoiceField(queryset=AuthUser.objects.all(), required=False)

    class Meta:
        model = SxLog
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.user = user
        # self.fields['user'].queryset = AuthUser.objects.filter(id=user.id)
        for nam, field in self.fields.items():
            field.disabled = True
        self.fields['alt_dx'].label = 'Alternate Diagnosis'


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
    post_code = forms.CharField(max_length=5, required=False)

    class Meta:
        model = Addresses
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
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
        # use_case = self.cleaned_data['use_case_address']

        if data == '':
            data = '11111'
        elif not re.search('\d{5}$', data):
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

        use_case = cleaned_data['use_case_address']
        if use_case and post_code == '':
            cleaned_data['post_code'] = "11111"
            # raise ValidationError(_('Invalid zip - Zip should be in the form ##### if not using the case address.'))

        print(cleaned_data)
        return cleaned_data


class AddContactAddressHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.form_tag = False
        self.disable_csrf = True
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
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
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
        self.form_tag = False
        self.disable_csrf = True
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
                      (0, 'Yes'),
                      (1, 'No'),
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
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            Row(
                Column('init_exposure', css_class='form-group col-md-4 mb-0'),
                Column('last_exposure', css_class='form-group col-md-4 mb-0'),
                Column('tent_qt_end', css_class='form-group col-md-4 mb-0'),
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

    def clean_can_quarantine(self):
        data = self.cleaned_data['can_quarantine']
        if data == '':
            data = None
        return data

    def clean_active(self):
        data = self.cleaned_data['active']
        if not data:
            data = True
        return data

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data['mark_as_contacted']:
            cleaned_data['last_follow'] = datetime.date.today()
        # cleaned_data['user'] = AuthUser.objects.get(id=self.user.id)
        return cleaned_data


class FollowUpContactForm(forms.ModelForm):

    init_exposure = forms.DateField(widget=DatePickerInput(), required=False)
    last_exposure = forms.DateField(widget=DatePickerInput(), required=False)
    tent_qt_end = forms.DateField(widget=DatePickerInput(), required=False)

    can_qt_options = [('', 'Unknown'),
                      (0, 'Yes'),
                      (1, 'No'),
                      ]
    can_quarantine = forms.TypedChoiceField(choices=can_qt_options, required=False)

    class Meta:
        model = Contacts
        exclude = ['person',
                   ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            Row(
                Column('init_exposure', css_class='form-group col-md-4 mb-0'),
                Column('last_exposure', css_class='form-group col-md-4 mb-0'),
                Column('tent_qt_end', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('can_quarantine', css_class='form-group col-md-4 mb-0'),
                Column('status', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
        )

    def clean_can_quarantine(self):
        data = self.cleaned_data['can_quarantine']
        if data == '':
            data = None
        return data

    def clean_active(self):
        data = self.cleaned_data['active']
        print("Cleaning FollowupContact, data is %s" % data)
        if data is None:
            data = True
        return data

    def clean(self):
        cleaned_data = super().clean()
        # if cleaned_data['mark_as_contacted']:
        #     cleaned_data['last_follow'] = datetime.date.today()
        # cleaned_data['user'] = AuthUser.objects.get(id=self.user.id)
        return cleaned_data


class TestFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.form_tag = False
        self.disable_csrf = True
        self.layout = Layout(
            Row(
                Column('sample_date', css_class='form-group col-md-4 mb-0'),
                Column('result_date', css_class='form-group col-md-4 mb-0'),
                Column('rcvd_date', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('result', css_class='form-group col-md-4 mb-0'),
                Column('user', css_class='form-group col-md-4 mb-0'),
                Column('logged_date', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
        )


class GetTest(forms.ModelForm):

    sample_date = forms.DateField(widget=DatePickerInput(), required=False)
    result_date = forms.DateField(widget=DatePickerInput(), required=False)
    rcvd_date = forms.DateField(widget=DatePickerInput(), required=False)

    result_choices = [('', '------'),
                      (1, 'Positive'),
                      (2, 'Negative'),
                      ]
    result = forms.TypedChoiceField(choices=result_choices)
    logged_date = forms.DateField(required=False)

    class Meta:
        model = Tests
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.user = user
        self.helper = FormHelper(self)
        # for nam, field in self.fields.items():
        #     field.disabled = True
        # self.fields['__all__'].widget.attrs['readonly'] = True
        # # self.fields['log_date'].widget.attrs['readonly'] = True
        # self.fields['__all__'].widget.attrs['disabled'] = True
        # # self.fields['log_date'].widget.attrs['disabled'] = True
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            Row(
                Column('sample_date', css_class='form-group col-md-4 mb-0'),
                Column('result_date', css_class='form-group col-md-4 mb-0'),
                Column('rcvd_date', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('result', css_class='form-group col-md-2 mb-0'),
                Column('test_type', css_class='form-group col-md-2 mb-0'),
                Column('user', css_class='form-group col-md-3 mb-0'),
                Column('logged_date', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
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
        # self.user = user
        self.fields['user'].queryset = AuthUser.objects.filter(id=user.id)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        # self.logged_date = datetime.date.today()

    def clean_status(self):
        return False

    def clean_logged_date(self):
        return datetime.date.today()

    # def clean(self):
        # self.logged_date = datetime.date.today()
        # super().clean()


class EmailForm(forms.ModelForm):

    email_address = forms.EmailField(required=False)

    class Meta:
        model = Emails
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            Div(
                Row(
                    Column('email_address', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                )
            )
        )


class EmailFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.form_tag = False
        self.disable_csrf = True
        self.layout = Layout(
            Div(
                Row(
                    Column('email_address', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                )
            )
        )


class AddContactEmailForm(forms.ModelForm):

    use_case_email = forms.BooleanField(required=False)
    email_address = forms.EmailField(required=False)

    class Meta:
        model = Emails
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            Div(
                Row(
                    Column('use_case_email', css_class='form-group col-md-5 mb-0'),
                    css_class='form-row'),
                Row(
                    Column('email_address', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                )
            )
        )


class AddContactEmailFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.form_tag = False
        self.disable_csrf = True
        self.layout = Layout(
            Div(
                Row(
                    Column('use_case_email', css_class='form-group col-md-5 mb-0'),
                    css_class='form-row'),
                Row(
                    Column('email_address', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                )
            )
        )


class AssignCaseForm(forms.ModelForm):
    assign_box = forms.BooleanField(required=False)
    case_id = forms.CharField(required=False)

    class Meta:
        model = Cases
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True

    def clean_case_id(self):
        print('cleaning')


class AssignContactForm(forms.ModelForm):
    assign_box = forms.BooleanField(widget=forms.CheckboxSelectMultiple, required=False)

    class Meta:
        model = Contacts
        fields = ['assign_box',
                  ]

