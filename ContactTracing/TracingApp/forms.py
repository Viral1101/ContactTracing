from django import forms
from django_localflavor_us.forms import USStateSelect, USZipCodeField, USPhoneNumberField
from django.forms import HiddenInput
from .models import *
from bootstrap_datepicker_plus import DatePickerInput
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from dateutil.relativedelta import relativedelta
import datetime
import re
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, Button, HTML
from crispy_forms.bootstrap import InlineRadios
from django.contrib.admin.widgets import FilteredSelectMultiple


class CaseLinkForm(forms.Form):
    cases = forms.ModelMultipleChoiceField(queryset=Cases.objects.all(),
                                            label=_('Select cases in this cluster'),
                                            required=False,
                                            widget=FilteredSelectMultiple(
                                                  _('cases'),
                                                  False,
                                            ))

    class Media:
        css = {
            'all': ('/static/admin/css/widgets.css',),
        }
        js = ('/admin/jsi18n',)


class ClusterEditForm(forms.ModelForm):
    is_index = forms.BooleanField(required=False)
    last_exposed = forms.DateField(widget=DatePickerInput(), required=False)
    index_case = forms.CharField(widget=forms.HiddenInput, required=False)
    # case = forms.CharField()

    class Meta:
        model = ClusterCaseJoin
        exclude = {'associated_contact',
                   'cluster'
                   }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.helper = FormHelper(self)
        self.fields['case'].disabled = True
        # case = self.instance.case
        # self.instance.case = str(Cases.objects.get(case_id=case))
        if self.instance.case == self.instance.index_case:
            self.fields['is_index'].widget.attrs['checked'] = True
        # self.fields['index_case'].initial = self.fields['case'].initial
        self.form_tag = False
        self.disable_csrf = True
        self.helper.layout = Layout(
            Column(
                Div(
                    Row(
                        Column('is_index', css_class='form-group col-md-1 mb-0 make_radio'),
                        Column('case', css_class='form-group col-md-4 mb-0'),
                        Column('last_exposed', css_class='form-group col-md-3 mb-0'),
                        Column('details', css_class='form-group col-md-4 mb-0'),
                        css_class='form-row',
                    ),
                    Row(
                        HTML("""<p>"""),
                        css_class='form-row',
                    )
                )
            )
        )

    def clean_index_case(self):
        data = self.cleaned_data['index_case']
        if data == '':
            index_case = None
        else:
            index_case = Cases.objects.filter(case_id=data).first()
        return index_case or None

    def clean(self):
        cleaned_data = super().clean()
        is_index = cleaned_data['is_index']

        if is_index:
            cleaned_data['last_exposed'] = None
            cleaned_data['details'] = None

        return cleaned_data


class ClusterEditFormOld(forms.Form):

    def __init__(self, *args, **kwargs):
        self.cluster = kwargs.get('cluster', None)
        del kwargs['cluster']
        super(ClusterEditForm, self).__init__(*args, **kwargs)
        qs = ClusterCaseJoin.objects.filter(cluster=self.cluster)
        self.fields['case'] = forms.ChoiceField(label='Select the index case:',
                                                choices=[(q.case.case_id, q.case) for q in qs],
                                                widget=forms.RadioSelect)
        # self.fields['details'] = forms.ChoiceField(widget=forms.Textarea, required=False)
        # self.fields['last_exposed'] = forms.DateField(widget=DatePickerInput(), required=False)
        self.form_method = 'post'
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Column(
                Row(
                    Column('case', css_class='form-group col-md-12 mb-0'),
                    # Column('last_exposed', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'),
                Row(
                    Column('details', css_class='form-group col-md-12 mb-0')
                    , css_class='form-row'),
                css_class='form-group col-md-12 mb-0'
            )
        )

        # print(cases)


class HouseHoldForm(forms.Form):
    people = forms.ModelMultipleChoiceField(queryset=Persons.objects.all(),
                                            label=_('Select people in this household'),
                                            required=False,
                                            widget=FilteredSelectMultiple(
                                                  _('people'),
                                                  False,
                                            ))

    class Media:
        css = {
            'all': ('/static/admin/css/widgets.css',),
        }
        js = ('/admin/jsi18n',)

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.form_method = 'post'
        # self.form_tag = False


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
            # print(self.cleaned_data['phone_id'])

        return cleaned_data


class AddressesForm(forms.ModelForm):
    address_id = forms.IntegerField(widget=forms.HiddenInput, required=False)
    street = forms.CharField(required=False)
    street2 = forms.CharField(required=False)
    city = forms.CharField(required=False)
    state = forms.CharField(widget=USStateSelect, initial='MO', required=False)
    post_code = forms.CharField(max_length=5, min_length=5, required=False)

    def clean_post_code(self):
        data = self.cleaned_data['post_code']

        if data == '':
            pass
        elif not re.search('\d{5}$', data):
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
                    Column('phone_number', css_class='form-group col-md-3 mb-0 phone'),
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
                    Column('phone_number', css_class='form-group col-md-3 mb-0 phone'),
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
                            # print(self.cleaned_data['address_id'])
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
    contact_pref = forms.ModelChoiceField(queryset=ContactPrefs.objects.all(), required=False)
    vacc_dose1 = forms.DateField(widget=DatePickerInput(), required=False)
    vacc_dose2 = forms.DateField(widget=DatePickerInput(), required=False)
    vacc_type1 = forms.ModelChoiceField(queryset=VaccineTypes.objects.all(), required=False)
    vacc_type2 = forms.ModelChoiceField(queryset=VaccineTypes.objects.all(), required=False)
    vacc_lot1 = forms.CharField(required=False)
    vacc_lot2 = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.fields['vacc_dose1'].label = 'Dose 1'
        self.fields['vacc_dose2'].label = 'Dose 2'
        self.fields['vacc_type1'].label = 'Dose 1 type'
        self.fields['vacc_type2'].label = 'Dose 2 type'
        self.fields['vacc_lot1'].label = 'Dose 1 lot'
        self.fields['vacc_lot2'].label = 'Dose 2 lot'
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            HTML("<h4>Personal Information</h4>"),
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
                Column('contact_pref', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            HTML("<h4>COVID Vaccine Info</h4>"),
            Row(
                Column('vacc_type1', css_class='form-group col-md-2 mb-0'),
                Column('vacc_dose1', css_class='form-group col-md-4 mb-0'),
                Column('vacc_lot1', css_class='form-group col-md-2 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('vacc_type2', css_class='form-group col-md-2 mb-0'),
                Column('vacc_dose2', css_class='form-group col-md-4 mb-0'),
                Column('vacc_lot2', css_class='form-group col-md-2 mb-0'),
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
    contact_pref = forms.ModelChoiceField(queryset=ContactPrefs.objects.all(), required=False)
    vacc_dose1 = forms.DateField(widget=DatePickerInput(), required=False)
    vacc_dose2 = forms.DateField(widget=DatePickerInput(), required=False)
    vacc_type1 = forms.ModelChoiceField(queryset=VaccineTypes.objects.all(), required=False)
    vacc_type2 = forms.ModelChoiceField(queryset=VaccineTypes.objects.all(), required=False)
    vacc_lot1 = forms.CharField(required=False)
    vacc_lot2 = forms.CharField(required=False)

    def clean_dob(self):
        data = self.cleaned_data['dob']

        if data is None:
            data = datetime.date(1900, 1, 1) #Set default birthday of 01 Jan 1900 for when birthday is left blank

        #     Date should only exist in the past
        if data >= datetime.date.today():
            # print('dob error')
            raise ValidationError(_('Invalid date - Date should be in the past'))

        return data

    def clean_age(self):
        data = self.cleaned_data['age']
        try:
            dob = self.cleaned_data['dob']
            if dob == datetime.datetime(1900, 1, 1):
                dob = None
        except KeyError:
            dob = None

        if not data:
            if dob:
                data = relativedelta(datetime.date.today(), dob).years

        return data

    def clean(self):
        # print("in clean")
        cleaned_data = super().clean()
        first = cleaned_data.get('first')
        last = cleaned_data.get('last')
        dob = cleaned_data.get('dob')
        # print(first)
        # print(last)
        # print(dob)

        try:
            if cleaned_data['pk']:
                return cleaned_data
        except KeyError:
            last_exists = Persons.objects.filter(last=last)
            if last_exists:
                # print("last exists")
                first_exists = last_exists.filter(first=first)
                if first_exists:
                    # print('first exists')
                    dob_exists = first_exists.filter(dob=dob)
                    if dob_exists:
                        # print('dob exists')
                        msg = "Person already exists. Check First name, Last name, and Date of Birth. " \
                              "Convert existing contact?"
                        self.add_error('first', msg)
        # print("end clean")
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
                  'contact_pref',
                  'vacc_dose1',
                  'vacc_dose2',
                  'vacc_type1',
                  'vacc_type2',
                  'vacc_lot1',
                  'vacc_lot2',
                  ]


class InvestigationCaseForm(forms.ModelForm):
    active = forms.BooleanField(widget=forms.HiddenInput, required=False)
    confirmed = forms.BooleanField(required=False)
    old_case_no = forms.CharField(max_length=15, required=False)
    # last_follow = forms.DateField(widget=DatePickerInput())
    release_date = forms.DateField(widget=DatePickerInput(), required=False)
    rel_pcp = forms.BooleanField(required=False)
    iso_pcp = forms.BooleanField(required=False)
    tent_release = forms.DateField(widget=DatePickerInput())
    reqs_pcp = forms.CharField(required=False)
    # release_date = forms.DateField(widget=DatePickerInput)
    last_follow = forms.DateField(required=False, widget=forms.HiddenInput)
    rel_pcp = forms.BooleanField(required=False)
    hospitalized = forms.BooleanField(required=False)
    icu = forms.BooleanField(required=False)
    onset_date = forms.DateField(widget=DatePickerInput(), required=False)
    # text_follow_up = forms.BooleanField(required=False)
    # email_follow_up = forms.BooleanField(required=False)

    class Meta:
            model = Cases
            exclude = ['test',
                       'person',
                       # 'old_case_no',
                       # 'release_date',
                       # 'tent_release',
                       ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rel_pcp'].label = 'Released by PCP'
        self.fields['iso_pcp'].label = 'Isolation Order by PCP'
        self.fields['reqs_pcp'].label = 'PCP requirements for release'
        self.fields['confirmed'].label = 'Positive Test Confirmation'
        self.fields['old_case_no'].label = 'Old ID'
        self.fields['monitor_not_case'].label = 'Not a case - Monitor'
        self.fields['icu'].label = 'Required ICU'
        self.fields['last_follow'].disabled = True
        # self.fields['tent_release'].label = 'Tentative Release Date'
        self.form_method = 'post'
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            HTML("<h4>Primary Care Info</h4>"),
            Row(
                Column('iso_pcp', css_class='form-group col-md-2 mb-0'),
                Column('reqs_pcp', css_class='form-group col-md-2 mb-0'),
                Column('rel_pcp', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            HTML("<h4>Case Data</h4>"),
            Row(
                Column('old_case_no', css_class='form-group col-md-4 mb-0'),
                Column('confirmed', css_class='form-group col-md-2 mb-0'),
                Column('probable', css_class='form-group col-md-2 mb-0'),
                Column('monitor_not_case', css_class='form-group col-md-2 mb-0'),
                Column('active', css_class='form-group col-md-2 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('onset_date', css_class='form-group col-md-4 mb-0'),
                Column('tent_release', css_class='form-group col-md-4 mb-0'),
                Column('release_date', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('hospitalized', css_class='form-group col-md-2 mb-0'),
                Column('icu', css_class='form-group col-md-2 mb-0'),
                Column('status', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            # Row(
            #     Column('text_follow_up', css_class='form-group col-md-4 mb-0'),
            #     Column('email_follow_up', css_class='form-group col-md-4 mb-0'),
            #     css_class='form-row'
            # ),
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

        if cleaned_data.get('status') != Statuses.objects.get(status_id=7):
            cleaned_data['last_follow'] = datetime.date.today()
        status = cleaned_data.get('status')
        release_date = cleaned_data.get('release_date')

        if release_date is None:
            if status == Statuses.objects.get(status_id=11):
                raise ValidationError(_('Release date cannot be empty if status is set to "Released".'))
        elif release_date > datetime.date.today():
            raise ValidationError(_('Release date cannot be a future date.'))

        return cleaned_data


class FollowUpCaseForm(forms.ModelForm):
    active = forms.BooleanField(widget=forms.HiddenInput(), required=False)
    confirmed = forms.BooleanField(required=False)
    # last_follow = forms.DateField(widget=DatePickerInput())
    release_date = forms.DateField(widget=DatePickerInput(), required=False)
    rel_pcp = forms.BooleanField(required=False)
    iso_pcp = forms.BooleanField(required=False)
    tent_release = forms.DateField(widget=DatePickerInput())
    reqs_pcp = forms.CharField(required=False)
    probable = forms.BooleanField(required=False)
    monitor_not_case = forms.BooleanField(required=False)
    old_case_no = forms.CharField(max_length=15, required=False)
    hospitalized = forms.BooleanField(required=False)
    icu = forms.BooleanField(required=False)
    onset_date = forms.DateField(widget=DatePickerInput(), required=False)
    # text_follow_up = forms.BooleanField(required=False)
    # email_follow_up = forms.BooleanField(required=False)

    class Meta:
        model = Cases
        exclude = ['test',
                   'person',
                   # 'old_case_no',
                   # 'release_date',
                   ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.fields['rel_pcp'].label = 'Released by PCP'
        self.fields['iso_pcp'].label = 'Isolation Order by PCP'
        self.fields['reqs_pcp'].label = 'PCP requirements for release'
        self.fields['confirmed'].label = 'Positive Test Confirmation'
        self.fields['monitor_not_case'].label = 'Not a Case - Monitor'
        self.fields['old_case_no'].label = 'Old ID'
        self.fields['icu'].label = 'Required ICU'
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            HTML("<h4>Primary Care Info</h4>"),
            Row(
                Column('iso_pcp', css_class='form-group col-md-2 mb-0'),
                Column('reqs_pcp', css_class='form-group col-md-2 mb-0'),
                Column('rel_pcp', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            HTML("<h4>Case Data</h4>"),
            Row(
                Column('old_case_no', css_class='form-group col-md-4 mb-0'),
                Column('confirmed', css_class='form-group col-md-2 mb-0'),
                Column('probable', css_class='form-group col-md-2 mb-0'),
                Column('monitor_not_case', css_class='form-group col-md-2 mb-0'),
                Column('active', css_class='form-group col-md-2 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('onset_date', css_class='form-group col-md-4 mb-0'),
                Column('tent_release', css_class='form-group col-md-4 mb-0'),
                Column('release_date', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('hospitalized', css_class='form-group col-md-2 mb-0'),
                Column('icu', css_class='form-group col-md-2 mb-0'),
                Column('status', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            # Row(
            #     Column('text_follow_up', css_class='form-group col-md-4 mb-0'),
            #     Column('email_follow_up', css_class='form-group col-md-4 mb-0'),
            #     css_class='form-row'
            # ),
            Column('active', css_class='form-group col-md-4 mb-0'),
        )

    def clean_status(self):
        cleaned_data = self.cleaned_data['status']
        # print(cleaned_data)
        # print(Statuses.objects.get(status_id=1))
        if cleaned_data == Statuses.objects.get(status_id=1):
            raise ValidationError(_('Invalid case status - Case should not still need investigation'))

        return cleaned_data

    #
    # def clean_last_follow(self):
    #     data = datetime.date.today()
    #     return data;

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        release_date = cleaned_data.get('release_date')
        if release_date is None:
            if status == Statuses.objects.get(status_id=11):
                raise ValidationError(_('Release date cannot be empty if status is set to "Released".'))
        elif release_date > datetime.date.today():
            raise ValidationError(_('Release date cannot be a future date.'))
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
        # print(data)
        # print(Statuses.objects.get(status_id=1))
        if data == Statuses.objects.get(status_id=1):
            raise ValidationError(_('Invalid case status - Case should not still need investigation'))
        return data
    #
    # def clean_last_follow(self):
    #     data = datetime.date.today()
    #     return data;


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
        cleaned_data['user'] = self.user
        # print(cleaned_data)
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
        # self.user = user
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
        # cleaned_data['user'] = self.user
        # print(cleaned_data)
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
        self.fields['vacc_dose1'].label = 'Dose 1'
        self.fields['vacc_dose2'].label = 'Dose 2'
        self.fields['vacc_type1'].label = 'Dose 1 type'
        self.fields['vacc_type2'].label = 'Dose 2 type'
        self.fields['vacc_lot1'].label = 'Dose 1 lot'
        self.fields['vacc_lot2'].label = 'Dose 2 lot'
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
                Column('contact_pref', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('vacc_type1', css_class='form-group col-md-2 mb-0'),
                Column('vacc_dose1', css_class='form-group col-md-4 mb-0'),
                Column('vacc_type2', css_class='form-group col-md-2 mb-0'),
                Column('vacc_dose2', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
        )


class ContactFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.form_tag = False
        self.disable_csrf = True
        self.fields['old_contact_no'].label = 'Old ID'
        self.layout = Layout(
            Row(
                Column('init_exposure', css_class='form-group col-md-4 mb-0'),
                Column('last_exposure', css_class='form-group col-md-4 mb-0'),
                Column('ten_qt_end', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('old_contact_no', css_class='form-group col-md-4 mb-0'),
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.user = user
        # self.fields['user'].queryset = AuthUser.objects.filter(id=user.id).first()
        # self.fields['user'].queryset = AuthUser.objects.filter(id=self.user)
        # self.fields['user'].queryset = self.user
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
        # cleaned_data['user'] = self.user
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
        self.helper = FormHelper(self)
        self.helper.disable_csrf = True
        self.helper.form_tag = False


class SymptomForm(forms.ModelForm):

    class Meta:
        model = Symptoms
        fields = '__all__'


class NewAssignment(forms.ModelForm):

    # status = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Assignments
        fields = ['user',
                  'assign_type',
                  ]

    def clean_user(self):
        data = self.cleaned_data['user']
        if data == AuthUser.objects.get(id=1):
            raise ValidationError(_('Admin may not be selected to for assignments.'))
        return data


class AddContactAddress(forms.ModelForm):

    # use_case_address = forms.BooleanField(required=False)
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
            # Row(
            #     Column('use_case_address', css_class='form-group col-md-5 mb-0'),
            #     css_class='form-row'
            # ),
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

        # use_case = cleaned_data['use_case_address']
        # if use_case and post_code == '':
        #     cleaned_data['post_code'] = "11111"
        #     # raise ValidationError(_('Invalid zip - Zip should be in the form ##### if not using the case address.'))

        print(cleaned_data)
        return cleaned_data


class AddContactAddressHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.form_tag = False
        self.disable_csrf = True
        self.layout = Layout(
            # Row(
            #     Column('use_case_address', css_class='form-group col-md-5 mb-0'),
            #     css_class='form-row'
            # ),
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
            # Row(
            #     Column('use_case_phone', css_class='form-group col-md-5 mb-0'),
            #     css_class='form-row'),
            Row(
                Column('phone_number', css_class='form-group col-md-3 mb-0 phone'),
                css_class='form-row'
            )
        )


class AddCasePhoneForContact(forms.Form):
    use_case_phone = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            Row(
                Column('use_case_phone', css_class='form-group col-md-5 mb-0'),
                css_class='form-row'
            ),
        )


class AddCaseEmailForContact(forms.Form):
    use_case_email = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            Row(
                Column('use_case_email', css_class='form-group col-md-5 mb-0'),
                css_class='form-row'
            ),
        )


class AddCaseAddressForContact(forms.Form):
    use_case_address = forms.BooleanField(required=False)

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
        )


class AddCaseRelation(forms.Form):

    relation_to_case = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            Row(
                Column('relation_to_case', css_class='form-group col-md-5 mb-0'),
                css_class='form-row'),
        )


class AddContactPhoneHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.form_tag = False
        self.disable_csrf = True
        self.layout = Layout(
            Row(
                Column('phone_number', css_class='form-group col-md-3 mb-0 phone'),
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
    old_contact_no = forms.CharField(max_length=15, required=False)
    status = forms.ModelChoiceField(queryset=Statuses.objects.all().exclude(status_id__in=[1, 3]))

    class Meta:
        model = Contacts
        exclude = ['person',
                   'init_exposure',
                   'last_exposure',
                   'tent_qt_end',
                   ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.fields['old_contact_no'].label = 'Old ID'
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            # Row(
            #     Column('init_exposure', css_class='form-group col-md-4 mb-0'),
            #     Column('last_exposure', css_class='form-group col-md-4 mb-0'),
            #     Column('tent_qt_end', css_class='form-group col-md-4 mb-0'),
            #     css_class='form-row'
            # ),
            Row(
                Column('old_contact_no', css_class='form-group col-md-4 mb-0'),
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

    # init_exposure = forms.DateField(widget=DatePickerInput(), required=False)
    # last_exposure = forms.DateField(widget=DatePickerInput(), required=False)
    # tent_qt_end = forms.DateField(widget=DatePickerInput(), required=False)

    can_qt_options = [('', 'Unknown'),
                      (0, 'Yes'),
                      (1, 'No'),
                      ]
    can_quarantine = forms.TypedChoiceField(choices=can_qt_options, required=False, coerce=int)
    active = forms.BooleanField(widget=forms.HiddenInput(), required=False)
    old_contact_no = forms.CharField(max_length=15, required=False)
    upgraded_case = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Contacts
        exclude = ['person',
                   'init_exposure',
                   'last_exposure',
                   'tent_qt_end',
                   ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.fields['old_contact_no'].label = 'Old ID'
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            Row(
                # Column('init_exposure', css_class='form-group col-md-4 mb-0'),
                # Column('last_exposure', css_class='form-group col-md-4 mb-0'),
                # Column('tent_qt_end', css_class='form-group col-md-4 mb-0'),
                # css_class='form-row'
            ),
            Row(
                Column('old_contact_no', css_class='form-group col-md-3 mb-0'),
                Column('can_quarantine', css_class='form-group col-md-3 mb-0'),
                Column('status', css_class='form-group col-md-3 mb-0'),
                Column('active', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),
        )

    def clean_upgraded_case(self):
        data = self.cleaned_data['upgraded_case']

        print("DATA: %s" % data)
        if data == '':
            data = None

        try:
            get_case = Cases.objects.get(case_id=data)
            print(get_case)
        except Cases.DoesNotExist:
            get_case = None
            print("None case")

        return get_case

    # def clean_can_quarantine(self):
    #     data = self.cleaned_data['can_quarantine']
    #     if data == '':
    #         data = None
    #     return data
    #
    # def clean_active(self):
    #     data = self.fields['active'].initial
    #     print("Cleaning FollowupContact, data is %s" % data)
    #     if data is None:
    #         data = True
    #     return data


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


class NewTestFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.form_tag = False
        self.disable_csrf = True
        self.layout = Layout(
            Div(
                Row(
                    Column('sample_date', css_class='form-group col-md-4 mb-0'),
                    Column('result_date', css_class='form-group col-md-4 mb-0'),
                    Column('rcvd_date', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('result', css_class='form-group col-md-2 mb-0'),
                    Column('test_type', css_class='form-group col-md-2 mb-0'),
                    Column('source', css_class='form-group col-md-3 mb-0'),
                    css_class='form-row'
                ),
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
    result = forms.ModelChoiceField(required=False, queryset=TestResults.objects.all())
    source = forms.ModelChoiceField(required=False, queryset=TestSources.objects.all())
    logged_date = forms.DateField(widget=forms.HiddenInput(), required=False)
    user = forms.ModelChoiceField(widget=forms.HiddenInput(), queryset=AuthUser.objects.all(), required=False)

    class Meta:
        model = Tests
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.user = user
        # self.fields['user'].queryset = AuthUser.objects.filter(id=user)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        # self.logged_date = datetime.date.today()
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
                Column('source', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),
        )

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

    # use_case_email = forms.BooleanField(required=False)
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
                # Row(
                #     Column('use_case_email', css_class='form-group col-md-5 mb-0'),
                #     css_class='form-row'),
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
                # Row(
                #     Column('use_case_email', css_class='form-group col-md-5 mb-0'),
                #     css_class='form-row'),
                Row(
                    Column('email_address', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                )
            )
        )


class AssignCaseForm(forms.Form):
    assign_box = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.form_tag = False
        self.disable_csrf = True
        self.empty_permitted = False


class AssignUploadedCaseForm(forms.Form):
    assign_box = forms.ModelChoiceField(queryset=AuthUser.objects.filter(id__gt=1), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.form_tag = False
        self.disable_csrf = True
        self.empty_permitted = False


class NewOutbreakForm(forms.ModelForm):

    class Meta:
        model = Outbreaks
        fields = {'date_of_exposure',
                  }


class NewLocation(forms.ModelForm):

    class Meta:
        model = Locations
        fields = {'name',
                  }


class NewOutbreakManager(forms.ModelForm):

    class Meta:
        model = OutbreakManagerJoin
        fields = {'position',
                  'person'
                  }


class ContactExposureForm(forms.ModelForm):

    initial_exposure = forms.DateField(widget=DatePickerInput(), required=False)
    last_exposure = forms.DateField(widget=DatePickerInput(), required=False)
    quarantine_end = forms.DateField(widget=DatePickerInput(), required=False)
    relation_to_case = forms.CharField(required=False)
    exposing_case = forms.ModelChoiceField(queryset=Cases.objects.all(), required=False)

    class Meta:
        model = Exposures
        fields = {'initial_exposure',
                  'last_exposure',
                  'quarantine_end',
                  'exposing_case',
                  'relation_to_case',
                  }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.form_tag = False
        self.disable_csrf = True
        self.layout = Layout(
            Div(
                Div(
                    Row(
                        Column('initial_exposure', css_class='form-group col-md-4 mb-0'),
                        Column('last_exposure', css_class='form-group col-md-4 mb-0'),
                        Column('quarantine_end', css_class='form-group col-md-4 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('exposing_case', css_class='form-group col-md-4 mb-0'),
                        Column('relation_to_case', css_class='form-group col-md-4 mb-0'),
                        Column('DELETE', css_class='form-group col-md-4 mb-0'),
                        css_class='form-row'
                    ),
                    css_class='form-row card'
                )
            )
        )


class ContactExposureFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.form_tag = False
        self.disable_csrf = True
        # self.render_unmentioned_fields = True
        self.layout = Layout(
            Div(
                Div(
                    Row(
                        Column('initial_exposure', css_class='form-group col-md-4 mb-0'),
                        Column('last_exposure', css_class='form-group col-md-4 mb-0'),
                        Column('quarantine_end', css_class='form-group col-md-4 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('exposing_case', css_class='form-group col-md-4 mb-0'),
                        Column('relation_to_case', css_class='form-group col-md-4 mb-0'),
                        Column('DELETE', css_class='form-group col-md-4 mb-0'),
                        css_class='form-row'
                    ),
                    css_class='form-row card'
                )
            )
        )


class ContactBulkForm(forms.Form):
    contacts = forms.ModelMultipleChoiceField(queryset=Contacts.objects.all(),
                                              label=_('Select contacts exposed by this case'),
                                              required=False,
                                              widget=FilteredSelectMultiple(_('contacts'),
                                                                            False,
                                                                            ))

    class Media:
        css = {
            'all': ('/static/admin/css/widgets.css',),
        }
        js = ('/admin/jsi18n',)


class ContactBulkEditForm(forms.ModelForm):

    initial_exposure = forms.DateField(widget=DatePickerInput(), required=False)
    last_exposure = forms.DateField(widget=DatePickerInput(), required=False)
    quarantine_end = forms.DateField(widget=DatePickerInput(), required=False)
    relation_to_case = forms.CharField(required=False)
    name = forms.CharField(required=False)
    exposure_id = forms.CharField(required=False)

    class Meta:
        model = Exposures
        fields = {'initial_exposure',
                  'last_exposure',
                  'quarantine_end',
                  'relation_to_case',
                  'exposure_id',
                  }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        print(self.instance)
        join_obj = ContactExposureJoin.objects.get(exposure=self.instance)
        self.initial['name'] = join_obj.contact
        self.initial['exposure_id'] = self.instance.exposure_id
        print(self.instance.exposure_id)
        self.fields['name'].disabled = True
        # self.form_tag = False
        # self.disable_csrf = True
        self.layout = Layout(
            Div(
                Div(
                    Div(
                        Row(
                            Column('name', css_class='form-group col-md-6 mb-0'),
                            Column('relation_to_case', css_class='form-group col-md-4 mb-0'),
                            Column('exposure_id', css_class='form-group col-md-2 mb-0'),
                            css_class='form-row'
                        ),
                        css_class='card-header'
                    ),
                    Div(
                        Row(
                            Column('initial_exposure', css_class='form-group col-md-4 mb-0'),
                            Column('last_exposure', css_class='form-group col-md-4 mb-0'),
                            Column('quarantine_end', css_class='form-group col-md-4 mb-0'),
                            css_class='form-row'
                        ),
                        css_class=' card-body'
                    ),
                    css_class='card'
                )
            )
        )


class ContactBulkEditFormHelper(FormHelper):

    class Meta:
        model = Exposures
        fields = {'initial_exposure',
                  'last_exposure',
                  'quarantine_end',
                  'relation_to_case',
                  'exposure_id',
                  }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        # self.form_tag = False
        # self.disable_csrf = True
        self.layout = Layout(
            Div(
                Div(
                    Div(
                        Row(
                            Column('name', css_class='form-group col-md-4 mb-0'),
                            Column('relation_to_case', css_class='form-group col-md-4 mb-0'),
                            Column('exposure_id', css_class='form-group col-md-2 mb-0'),
                            css_class='form-row'
                        ),
                        css_class='card-header'
                    ),
                    Div(
                        Row(
                            Column('initial_exposure', css_class='form-group col-md-4 mb-0'),
                            Column('last_exposure', css_class='form-group col-md-4 mb-0'),
                            Column('quarantine_end', css_class='form-group col-md-4 mb-0'),
                            css_class='form-row'
                        ),
                        css_class=' card-body'
                    ),
                    css_class='card'
                )
            )
        )


class LogEditForm(forms.ModelForm):

    previous_text = forms.CharField(widget=forms.Textarea())
    edit_reason = forms.CharField()
    log = forms.ModelChoiceField(queryset=TraceLogs.objects.none())
    page = ''
    ctype = ''
    pid = ''
    cancel_url = ''

    class Meta:
        model = LogEdits
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        self.page = kwargs.pop('page', None)
        self.ctype = kwargs.pop('ctype', None)
        self.pid = kwargs.pop('pid', None)
        self.cancel_url = f'/{self.page}/{self.ctype}/{self.pid}'
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        # self.form_tag = False
        # self.disable_csrf = True
        self.fields['log'].widget = HiddenInput()
        self.fields['user'].widget = HiddenInput()
        self.fields['edit_date'].widget = HiddenInput()
        self.fields['log'].required = False
        self.fields['user'].required = False
        self.fields['edit_date'].required = False
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('previous_text', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('edit_reason', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Submit('save_and_return', 'Save and Return', css_class='btn btn-success col-md-2 mr-md-3'),
            Button('cancel', 'Cancel',
                   css_class='btn btn-danger col-md-2 mr-md-3',
                   onclick="window.location.href = '{}';".format(self.cancel_url)),
        )
        self.helper.render_hidden_fields = False
