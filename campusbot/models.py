from django.db import models
 
# Create your models here.

from django.contrib.auth.models import User

class ChatSession(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="chat_sessions"
    )
    title = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ChatMessage(models.Model):
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    sender = models.CharField(max_length=10)   # "user" or "bot"
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class FAQ(models.Model):
    CATEGORY_CHOICES = [
        ('academic', 'Academic'),
        ('admission', 'Admission'),
        ('fees', 'Fees'),
        ('hostel', 'Hostel'),
        ('general', 'General'),
    ]

    question = models.CharField(max_length=500, help_text="The main way a student might phrase this question")
    answer = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    # Comma-separated alternate phrasings, e.g. "ut date, exam schedule, when is unit test"
    keywords = models.CharField(max_length=500, blank=True, help_text="Comma-separated alternate phrasings/keywords")

    def __str__(self):
        return self.question

