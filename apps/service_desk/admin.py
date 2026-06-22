from django.contrib import admin
from .models import TicketCategory, HRTicket, TicketComment, KnowledgeCategory, KnowledgeArticle, SatisfactionSurvey

admin.site.register(TicketCategory)
admin.site.register(HRTicket)
admin.site.register(TicketComment)
admin.site.register(KnowledgeCategory)
admin.site.register(KnowledgeArticle)
admin.site.register(SatisfactionSurvey)
