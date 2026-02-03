"""
=============================================================================
Quizfy Forms
=============================================================================

This module defines all Django forms for the Quizfy quiz platform.

Form Categories:
----------------
Authentication Forms:
    - TeacherLoginForm      : Login form for teachers
    - TeacherSignupForm     : Registration form for teachers
    - StudentSignupForm     : Registration form for students
    - StudentLoginForm      : Login form for students (supports email or username)
    - ChangePasswordForm    : Password change for logged-in users

Quiz Management Forms:
    - QuizForm              : Create/edit quiz basic info
    - QuizSettingsForm      : Configure quiz timer, due date, active status
    - QuestionForm          : Create multiple choice questions
    - TrueFalseQuestionForm : Create true/false questions
    - FileUploadQuestionForm: Create file upload questions

Student Forms:
    - EnterQuizForm         : Enter quiz code to access a quiz
    - FileUploadSubmissionForm : Upload files for file-type questions

Organization Forms:
    - FolderForm            : Create subject folders
    - MoveQuizForm          : Move quiz between folders

Author: Quizfy Team
=============================================================================
"""

import re
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import Quiz, Question, StudentProfile, SubjectFolder


# =============================================================================
# AUTHENTICATION FORMS - TEACHER
# =============================================================================

class TeacherLoginForm(forms.Form):
    """
    Simple login form for teachers.
    Uses username and password authentication.
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "placeholder": "Username",
            "autocomplete": "username",
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": "Password",
            "autocomplete": "current-password",
        })
    )


class TeacherSignupForm(forms.ModelForm):
    """
    Registration form for teacher accounts.
    
    Teachers can create quizzes, view submissions, and grade students.
    Sets is_staff=True on the User model.
    """
    password1 = forms.CharField(
        label="Password", 
        widget=forms.PasswordInput(attrs={"placeholder": "Password"})
    )
    password2 = forms.CharField(
        label="Confirm Password", 
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm password"})
    )

    class Meta:
        model = User
        fields = ["username", "email"]

    def clean(self):
        """Validate that both passwords match."""
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            raise forms.ValidationError("Passwords do not match")
        return cleaned


# =============================================================================
# AUTHENTICATION FORMS - STUDENT
# =============================================================================

def _slugify_simple(value: str) -> str:
    """
    Create a simple slug from a string.
    Removes spaces and special characters, returns lowercase alphanumeric.
    """
    value = value.strip().lower()
    value = re.sub(r"\s+", "", value)
    value = re.sub(r"[^a-z0-9]", "", value)
    return value


class StudentSignupForm(UserCreationForm):
    """
    Registration form for student accounts.
    
    Collects:
    - Full name (first, second, third - Arabic naming convention)
    - University ID (unique identifier)
    - City and Major
    - Email (for password recovery)
    
    Automatically generates a username from name + last 3 digits of university ID.
    """
    
    # Name fields
    first_name = forms.CharField(
        max_length=60,
        widget=forms.TextInput(attrs={"placeholder": "First name"})
    )
    second_name = forms.CharField(
        max_length=60,
        widget=forms.TextInput(attrs={"placeholder": "Second name"})
    )
    third_name = forms.CharField(
        max_length=60,
        widget=forms.TextInput(attrs={"placeholder": "Third name"})
    )

    # University information
    university_id = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={"placeholder": "University ID"})
    )
    city = forms.ChoiceField(choices=StudentProfile.CITY_CHOICES)
    major = forms.ChoiceField(choices=StudentProfile.MAJOR_CHOICES)

    # Contact
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"placeholder": "Email address"})
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "second_name",
            "third_name",
            "university_id",
            "city",
            "major",
            "email",
            "password1",
            "password2",
        )

    def clean_university_id(self):
        """Ensure university ID is unique."""
        uni_id = self.cleaned_data["university_id"]
        if StudentProfile.objects.filter(university_id=uni_id).exists():
            raise forms.ValidationError("University ID already exists.")
        return uni_id

    def clean_email(self):
        """Normalize email and ensure it's unique."""
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered.")
        return email

    def _generate_username(self, base: str) -> str:
        """Generate unique username, appending numbers if needed."""
        username = base
        counter = 1
        while User.objects.filter(username=username).exists():
            counter += 1
            username = f"{base}{counter}"
        return username

    def save(self, commit=True):
        """
        Save the user with auto-generated username.
        Username format: firstsecondthird123 (last 3 digits of university ID)
        """
        user = super().save(commit=False)

        first = self.cleaned_data["first_name"]
        second = self.cleaned_data["second_name"]
        third = self.cleaned_data["third_name"]
        uni_id = self.cleaned_data["university_id"]

        # Generate username from name + last 3 digits of university ID
        base_username = _slugify_simple(f"{first}{second}{third}{uni_id[-3:]}")
        user.username = self._generate_username(base_username)

        user.first_name = first
        user.last_name = f"{second} {third}"
        user.email = self.cleaned_data["email"].lower()
        user.is_staff = False  # Students are not staff

        if commit:
            user.save()

        return user


class StudentLoginForm(AuthenticationForm):
    """
    Login form for students that supports both username and email.
    
    Students can log in using:
    - Their auto-generated username
    - Their registered email address
    
    The form automatically translates email to username before authentication.
    """

    def clean_username(self):
        """Convert email to username if email was entered."""
        identifier = (self.cleaned_data.get("username") or "").strip()

        # If user entered an email, find the associated username
        if "@" in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
            if user:
                return user.username

        return identifier


# =============================================================================
# PASSWORD MANAGEMENT
# =============================================================================

class ChangePasswordForm(forms.Form):
    """
    Form for logged-in users to change their password.
    
    Requires:
    - Current password (for verification)
    - New password (entered twice for confirmation)
    """
    
    old_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your current password",
            "autocomplete": "current-password",
        })
    )
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Enter new password",
            "autocomplete": "new-password",
        })
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Confirm new password",
            "autocomplete": "new-password",
        })
    )

    def __init__(self, user, *args, **kwargs):
        """Store the user instance for password verification."""
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        """Verify the current password is correct."""
        old_password = self.cleaned_data.get("old_password")
        if not self.user.check_password(old_password):
            raise forms.ValidationError(
                "Your old password was entered incorrectly. Please try again."
            )
        return old_password

    def clean_new_password2(self):
        """Ensure both new password fields match."""
        new_password1 = self.cleaned_data.get("new_password1")
        new_password2 = self.cleaned_data.get("new_password2")
        
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise forms.ValidationError("The two password fields didn't match.")
        
        return new_password2

    def save(self):
        """Update the user's password."""
        self.user.set_password(self.cleaned_data["new_password1"])
        self.user.save()
        return self.user


# =============================================================================
# QUIZ MANAGEMENT FORMS
# =============================================================================

class QuizForm(forms.ModelForm):
    """
    Form for creating a new quiz.
    
    Fields:
    - title: Quiz name displayed to students
    - quiz_type: Multiple choice, true/false, or file upload
    - folder: Optional subject folder for organization
    """
    
    class Meta:
        model = Quiz
        fields = ["title", "quiz_type", "folder"]

    def __init__(self, *args, **kwargs):
        # Pop teacher from kwargs before calling super()
        teacher = kwargs.pop("teacher", None)
        super().__init__(*args, **kwargs)

        self.fields["title"].widget.attrs.update({"placeholder": "Quiz title"})
        self.fields["quiz_type"].widget.attrs.update({"class": "quiz-type-select"})

        # Filter folders to only show this teacher's folders
        if teacher:
            self.fields["folder"].queryset = teacher.folders.all()


class QuizSettingsForm(forms.ModelForm):
    """
    Form for editing quiz settings.
    
    Settings:
    - due_at: Optional deadline after which quiz closes
    - duration_minutes: Optional time limit in minutes
    - is_active: Whether students can access the quiz
    """
    
    class Meta:
        model = Quiz
        fields = ["due_at", "duration_minutes", "is_active"]
        widgets = {
            "due_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "duration_minutes": forms.NumberInput(attrs={
                "type": "number",
                "min": 1,
                "placeholder": "e.g. 15"
            }),
        }


# =============================================================================
# QUESTION FORMS
# =============================================================================

class QuestionForm(forms.ModelForm):
    """
    Form for creating Multiple Choice questions.
    
    Features:
    - Question text
    - Optional image
    - 4 answer options
    - Correct answer selection
    """
    
    class Meta:
        model = Question
        fields = [
            "text",
            "image",
            "option1",
            "option2",
            "option3",
            "option4",
            "correct_option",
        ]
        widgets = {
            "text": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Enter your question"
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Simplify correct answer choices for multiple choice
        self.fields["correct_option"].choices = [
            (1, 'Option 1'), 
            (2, 'Option 2'), 
            (3, 'Option 3'), 
            (4, 'Option 4')
        ]


class TrueFalseQuestionForm(forms.ModelForm):
    """
    Form for creating True/False questions.
    
    Automatically sets:
    - option1 = "True"
    - option2 = "False"
    - question_type = "true_false"
    """
    
    class Meta:
        model = Question
        fields = ["text", "image", "correct_option"]
        widgets = {
            "text": forms.Textarea(attrs={
                "rows": 3, 
                "placeholder": "Enter your True/False question"
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show True/False options
        self.fields["correct_option"].choices = [
            (1, 'True'), 
            (2, 'False')
        ]
        self.fields["correct_option"].label = "Correct Answer"
    
    def save(self, commit=True):
        """Save with true/false question type and preset options."""
        instance = super().save(commit=False)
        instance.question_type = 'true_false'
        instance.option1 = 'True'
        instance.option2 = 'False'
        instance.option3 = ''
        instance.option4 = ''
        if commit:
            instance.save()
        return instance


class FileUploadQuestionForm(forms.ModelForm):
    """
    Form for creating File Upload questions.
    
    Students will upload a file (PDF, JPG, PNG) as their answer.
    These questions are graded manually by the teacher.
    """
    
    class Meta:
        model = Question
        fields = ["text", "image"]
        widgets = {
            "text": forms.Textarea(attrs={
                "rows": 3, 
                "placeholder": "Enter instructions for what the student should upload"
            }),
        }
    
    def save(self, commit=True):
        """Save with file_upload question type."""
        instance = super().save(commit=False)
        instance.question_type = 'file_upload'
        instance.option1 = ''
        instance.option2 = ''
        instance.option3 = ''
        instance.option4 = ''
        instance.correct_option = 1  # Default value (not used for file uploads)
        if commit:
            instance.save()
        return instance


# =============================================================================
# STUDENT QUIZ ACCESS FORMS
# =============================================================================

class EnterQuizForm(forms.Form):
    """
    Form for students to enter a quiz code.
    Used on the student dashboard to access a quiz.
    """
    quiz_code = forms.CharField(
        max_length=10,
        label="Quiz Code",
        widget=forms.TextInput(attrs={
            "placeholder": "Enter quiz code",
            "autocomplete": "off",
        }),
    )


class FileUploadSubmissionForm(forms.Form):
    """
    Form for students to upload files for file-type questions.
    
    Validation:
    - Maximum file size: 10MB
    - Allowed formats: PDF, JPG, JPEG, PNG
    """
    file = forms.FileField(
        label="Upload your file",
        help_text="Accepted formats: PDF, JPG, PNG (Max 10MB)",
        widget=forms.FileInput(attrs={"accept": ".pdf,.jpg,.jpeg,.png"})
    )
    
    def clean_file(self):
        """Validate file size and type."""
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (10MB max)
            max_size = 10 * 1024 * 1024  # 10MB in bytes
            if file.size > max_size:
                raise forms.ValidationError("File size must be under 10MB")
            
            # Check file extension
            ext = file.name.split('.')[-1].lower()
            allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png']
            if ext not in allowed_extensions:
                raise forms.ValidationError("Only PDF, JPG, and PNG files are allowed")
        return file


# =============================================================================
# FOLDER MANAGEMENT FORMS
# =============================================================================

class FolderForm(forms.ModelForm):
    """
    Form for creating a subject folder.
    Used to organize quizzes by subject/course.
    """
    
    class Meta:
        model = SubjectFolder
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "Folder name (e.g., Physics 101)"
            })
        }


class MoveQuizForm(forms.Form):
    """
    Form for moving a quiz to a different folder.
    
    Options:
    - Select a folder to move the quiz into
    - Select "Ungrouped" to remove from any folder
    """
    folder = forms.ModelChoiceField(
        queryset=SubjectFolder.objects.none(),
        required=False,
        empty_label="— Ungrouped —",
        label="Move to folder",
    )

    def __init__(self, *args, **kwargs):
        # Pop teacher from kwargs before calling super()
        teacher = kwargs.pop("teacher", None)
        super().__init__(*args, **kwargs)

        # Filter folders to only show this teacher's folders
        if teacher:
            self.fields["folder"].queryset = SubjectFolder.objects.filter(
                teacher=teacher
            ).order_by("name")