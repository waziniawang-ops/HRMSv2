from django.contrib import admin
from .models import BenefitPlan, EligibilityRule, BenefitEnrollment, BenefitDependent, BenefitClaimReference, BenefitCost

admin.site.register(BenefitPlan)
admin.site.register(EligibilityRule)
admin.site.register(BenefitEnrollment)
admin.site.register(BenefitDependent)
admin.site.register(BenefitClaimReference)
admin.site.register(BenefitCost)
