from django.db import models
class Feedback(models.Model):
 ticket_text=models.TextField()
 predicted_queue=models.CharField(max_length=80)
 corrected_queue=models.CharField(max_length=80)
 created_at=models.DateTimeField(auto_now_add=True)
