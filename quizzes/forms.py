from django import forms 
from django.contrib.auth.models import User
from .models import Quiz,Question,StudentProfile,SubjectFolder


class TeacherLoginForm(forms.Form):
    username=forms.CharField()
    password=forms.CharField(widget=forms.PasswordInput)

class TeacherSignupForm(forms.ModelForm):
    password1=forms.CharField(label='Password',widget=forms.PasswordInput)
    password2=forms.CharField(label='Confirm Password',widget=forms.PasswordInput)
    
    class Meta:
        model= User
        fields=['username','email']
        
    def clean(self):
        cleaned=super().clean()
        
        if cleaned.get('password1') != cleaned.get('password2'):
            raise forms.ValidationError('Passwords do not match')
        return cleaned
class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ["title", "folder"]

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop("teacher", None)
        super().__init__(*args, **kwargs)

        if teacher:
            self.fields["folder"].queryset = SubjectFolder.objects.filter(teacher=teacher).order_by("name")

        # optional nice labels
        self.fields["title"].widget.attrs.update({"placeholder": "Quiz title"})

class QuestionForm(forms.ModelForm):
    class Meta:
        model= Question
        fields=['text','image','option1','option2','option3','option4','correct_option']
        
        widgets={
            'text':forms.Textarea(attrs={'rows':3})
        }
class EnterQuizForm(forms.Form):
    quiz_code = forms.CharField(
        max_length=10,
        label="Quiz Code",
        widget=forms.TextInput(attrs={"placeholder": "Enter quiz code"})
    )

    
class StudentLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class StudentSignupForm(forms.ModelForm):
    # profile fields
    first_name = forms.CharField(max_length=60)
    second_name = forms.CharField(max_length=60)
    third_name = forms.CharField(max_length=60)

    university_id = forms.CharField(max_length=30)
    city = forms.ChoiceField(choices=StudentProfile.CITY_CHOICES)
    section = forms.CharField(max_length=20)
    major = forms.ChoiceField(choices=StudentProfile.MAJOR_CHOICES)

    # auth fields
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["username", "email"]  # username used for login

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned

    def clean_university_id(self):
        uni_id = self.cleaned_data["university_id"].strip()
        if StudentProfile.objects.filter(university_id=uni_id).exists():
            raise forms.ValidationError("University ID already exists.")
        return uni_id  
    
class FolderForm(forms.ModelForm):
    class Meta:
        model = SubjectFolder
        fields = ["name"]
from django import forms
from .models import SubjectFolder, Quiz


class MoveQuizForm(forms.Form):
    folder = forms.ModelChoiceField(
        queryset=SubjectFolder.objects.none(),
        required=False,
        empty_label="— Ungrouped —",
        label="Move to folder"
    )

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop("teacher", None)
        super().__init__(*args, **kwargs)

        if teacher:
            self.fields["folder"].queryset = SubjectFolder.objects.filter(
                teacher=teacher
            ).order_by("name")
