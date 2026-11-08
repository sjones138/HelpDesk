from django.contrib import admin
from .models import Feedback
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
 list_display=('predicted_queue','corrected_queue','created_at')
 readonly_fields=('ticket_text','predicted_queue','corrected_queue','created_at')
