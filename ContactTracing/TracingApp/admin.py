from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Persons)
admin.site.register(Assignments)
admin.site.register(Addresses)
admin.site.register(PersonPhoneJoin)
admin.site.register(PersonAddressJoin)
admin.site.register(PersonEmailJoin)
admin.site.register(Emails)
admin.site.register(Phones)
admin.site.register(Cases)
admin.site.register(SymptomDefs)
admin.site.register(Symptoms)
admin.site.register(SxStates)
admin.site.register(SxLog)
admin.site.register(SxLogJoin)
admin.site.register(CaseSxJoin)
admin.site.register(ContactSxJoin)
admin.site.register(TraceLogs)
admin.site.register(CaseLogJoin)
admin.site.register(Contacts)
admin.site.register(ContactLogJoin)
admin.site.register(ContactPrefs)
admin.site.register(Exposures)
admin.site.register(ContactExposureJoin)
