from django.contrib import admin
from .models import ClaimType, ExpensePolicy, ClaimRequest, ClaimLine, ClaimReceipt, TravelRequest

admin.site.register(ClaimType)
admin.site.register(ExpensePolicy)
admin.site.register(ClaimRequest)
admin.site.register(ClaimLine)
admin.site.register(ClaimReceipt)
admin.site.register(TravelRequest)
