from django import forms
from django_localflavor_us.forms import USStateSelect, USZipCodeField, USPhoneNumberField
from .models import *
from bootstrap_datepicker_plus import DatePickerInput
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

import datetime
import re


class NewPhoneNumberForm(forms.ModelForm):

    class Meta:
        model = Phones
        fields = '__all__'


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
                    (1, "Jr"),
                    (2, "Sr"),
                    (3, "II"),
                    (4, "III"),
                    (5, "IV")]

    suffix = forms.TypedChoiceField(choices=suff_options, coerce=str, required=False)

    sexes = [('', '------'),
             (0, "Female"),
             (1, "Male")]

    sex = forms.TypedChoiceField(choices=sexes, coerce=str)
    dob = forms.DateField(widget=DatePickerInput(), required=False)

    def clean_dob(self):
        data = self.cleaned_data['dob']

        #     Date should only exist in the past
        if data >= datetime.date.today():
            raise ValidationError(_('Invalid date - Date should be in the past'))

        return data

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


class CaseForm(forms.Form):

    # Phone Number
    phone_number = USPhoneNumberField(required=False)

    # def clean_phone_number(self):
    #     data = self.cleaned_data['phone_number']
    #
    #     # Valid phone numbers are in 10 or 11 digit form
    #     # 5551234646
    #     # 15551234646
    #     if not re.search('1?\d{10}$', data):
    #         raise ValidationError(_('Invalid phone number - Phone number should be 10 or 11 digits'))
    #
    #     return data

    # Test Details
    positive_result = forms.BooleanField()
    test_type = forms.ModelChoiceField(queryset=TestTypes.objects.all())
    test_date = forms.DateField(widget=DatePickerInput())
    result_date = forms.DateField(widget=DatePickerInput())
    received_date = forms.DateField(widget=DatePickerInput())

    def clean_test_date(self):
        data = self.cleaned_data['test_date']

    #     Date should only exist in the past
        if data >= datetime.date.today():
            raise ValidationError(_('Invalid date - Date should be in the past'))

        return data

    def clean_result_date(self):
        data = self.cleaned_data['result_date']

    #     Date cannot be in the future
        if data > datetime.date.today():
            raise ValidationError(_('Invalid date - Date cannot be in the future'))

        return data

    def clean_received_date(self):
        data = self.cleaned_data['received_date']

    #     Date cannot be in the future
        if data > datetime.date.today():
            raise ValidationError(_('Invalid date - Date cannot be in the future'))

        return data

    # Assignments
    assign_to = forms.ModelChoiceField(queryset=AuthUser.objects.all())
    assignment_type = forms.ModelChoiceField(queryset=AssignmentType.objects.all())
