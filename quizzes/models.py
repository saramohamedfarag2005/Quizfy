from django.db import models
from django.contrib.auth.models import User
import secrets
from django.core.validators import RegexValidator

numeric_only=RegexValidator(
    regex=r'^\d+$',
    message='University ID must contain digits only'
)

def question_image_upload_path(instance, filename):
    return f'quiz_images/quiz_{instance.quiz.id}/{filename}'
    

class Quiz(models.Model):
    title=models.CharField(max_length=60)
    code=models.CharField(max_length=40,unique=True,blank=True,null=True)
    teacher=models.ForeignKey(User, on_delete=models.CASCADE,related_name='quizzes')
    created_at=models.DateTimeField(auto_now_add=True)
    folder = models.ForeignKey(
    "SubjectFolder", on_delete=models.SET_NULL,
    null=True, blank=True, related_name="quizzes"
)

    def save(self,*args,**kwargs):
        if not self.code:
            self.code=secrets.token_hex(3).upper()
        super().save(*args,**kwargs)

    def __str__(self):
        return f'{self.title} - {self.code}'

class Question(models.Model):
    quiz=models.ForeignKey(Quiz,on_delete=models.CASCADE,related_name='questions')
    text=models.TextField(blank=True)
    image=models.ImageField(upload_to=question_image_upload_path, blank=True , null=True)
    option1=models.CharField(max_length=60)
    option2=models.CharField(max_length=60)
    option3=models.CharField(max_length=60)
    option4=models.CharField(max_length=60)
    correct_option=models.IntegerField(choices=[
        (1,'Option 1'),(2,'Option 2'),(3,'Option 3'),(4,'Option 4')
    ])
    def option_text(self,number):
        return {
            1:self.option1,
            2:self.option2,
            3:self.option3,
            4:self.option4,
        }.get(number,"(blank)")               

    def __str__(self):
        return self.text[:60] if self.text else f"Question {self.id}"

class Submission(models.Model):
    quiz=models.ForeignKey(Quiz,on_delete=models.CASCADE, related_name='submissions')
    student_name=models.CharField(max_length=60)
    score=models.IntegerField()
    total=models.IntegerField()
    submitted_at=models.DateTimeField(auto_now_add=True)
    student_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="submissions"
    )

    def __str__(self):
        return f"{self.student_name} - {self.quiz.code} ({self.score}/{self.total})"
class Answer(models.Model):
    submission=models.ForeignKey(Submission,on_delete=models.CASCADE,related_name='answers')
    question=models.ForeignKey(Question,on_delete=models.CASCADE)
    selected=models.IntegerField(null=True,blank=True)
    is_correct=models.BooleanField(default=False)
class StudentProfile(models.Model):
    CITY_CHOICES = [
        ("Riyadh", "Riyadh"),
        ("Jeddah", "Jeddah"),
        ("Mecca", "Mecca"),
        ("Medina", "Medina"),
    ]

    MAJOR_CHOICES = [
        ("CS", "Computer Science"),
        ("IT", "Information Technology"),
        ("BUS", "Business"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")

    first_name = models.CharField(max_length=60)
    second_name = models.CharField(max_length=60)
    third_name = models.CharField(max_length=60)

    university_id = models.CharField(max_length=30, unique=True,validators=[numeric_only])

    city = models.CharField(max_length=20, choices=CITY_CHOICES)
    section = models.CharField(max_length=20,validators=[numeric_only])

    major = models.CharField(max_length=10, choices=MAJOR_CHOICES)

    def __str__(self):
        return f"{self.first_name} {self.second_name} ({self.university_id})"

class SubjectFolder(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="folders")
    name = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("teacher", "name")

    def __str__(self):
        return f"{self.name} ({self.teacher.username})"

# Create your models here.
