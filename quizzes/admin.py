from django.contrib import admin
from .models import Quiz,Question,Submission,Answer,StudentProfile

admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Submission)
admin.site.register(Answer)
admin.site.register(StudentProfile)

# Register your models here.
