from django.contrib import admin
from .models import DocCategory, DocTemplate, DocRecord, DocPolicy, DocAcknowledgement, RetentionRule

admin.site.register(DocCategory)
admin.site.register(DocTemplate)
admin.site.register(DocRecord)
admin.site.register(DocPolicy)
admin.site.register(DocAcknowledgement)
admin.site.register(RetentionRule)
