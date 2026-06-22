from django.contrib import admin
from .models import (
    OffboardingCase, ClearanceTask, AssetClearance,
    AccessRevocation, ExitInterview, FinalSettlement,
)

admin.site.register(OffboardingCase)
admin.site.register(ClearanceTask)
admin.site.register(AssetClearance)
admin.site.register(AccessRevocation)
admin.site.register(ExitInterview)
admin.site.register(FinalSettlement)
