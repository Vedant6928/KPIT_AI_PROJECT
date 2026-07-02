from django.db import models
 
# Create your models here.
 

class Register_details(models.Model):
    fname = models.CharField(max_length=50)
    lname = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)


    def __str__(self):
        return self.fname
    

