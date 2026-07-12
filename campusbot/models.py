from django.db import models
 
# Create your models here.
 

class Register_details(models.Model):
    fname = models.CharField(max_length=50)
    lname = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)


    def __str__(self):
        return self.fname


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

