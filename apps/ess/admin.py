from django.contrib import admin
from .models import ESSRequestType, ESSRequest, ProfileChangeRequest, ManagerDelegation

admin.site.register(ESSRequestType)
admin.site.register(ESSRequest)
admin.site.register(ProfileChangeRequest)
admin.site.register(ManagerDelegation)
