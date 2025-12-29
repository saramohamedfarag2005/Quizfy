from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from .models import Quiz,Question,Submission,Answer,StudentProfile,SubjectFolder
from .forms import (
    TeacherLoginForm,TeacherSignupForm,QuizForm,QuestionForm,EnterQuizForm, StudentSignupForm, StudentLoginForm,FolderForm,MoveQuizForm,
)
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
import difflib
import re


def home(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("teacher_quizzes")
        return redirect("student_dashboard")
    return render(request, "quizzes/home.html")

def student_required(view_func):
    return user_passes_test(
        lambda u: u.is_authenticated and not u.is_staff and hasattr(u, "student_profile"),
        login_url="/student/login/"
    )(view_func)

def staff_required(view_func):
    return user_passes_test(
        lambda u: u.is_authenticated and u.is_staff,
        login_url="/teacher/login/"
    )(view_func)




# --- Teacher Help Bot (FAQ + fuzzy match) ---

TEACHER_KB = [
    {
        "tags": ["create folder", "subject folder", "add subject", "new folder", "folder"],
        "q": "How do I create a subject folder?",
        "a": (
            "Go to **My Subjects** → click **+ Create Subject Folder** → type the subject name (e.g., Physics) → Save.\n\n"
            "After that, you can move quizzes into it using **Move** on any quiz."
        )
    },
    {
        "tags": ["move quiz", "assign quiz", "put quiz in folder", "organize quizzes", "ungrouped"],
        "q": "How do I move a quiz into a folder?",
        "a": (
            "On the teacher dashboard, find the quiz (especially under **Ungrouped Quizzes**) → click **Move** → select the folder → Save."
        )
    },
    {
        "tags": ["export", "excel", "download", "submissions file", "xlsx"],
        "q": "How do I export submissions to Excel?",
        "a": (
            "You have two options:\n"
            "1) Export a single quiz: open the quiz card → click **Export Excel**.\n"
            "2) Export a whole subject folder: open the folder card → click **Export Excel**.\n\n"
            "The file includes: student full name, university ID, section, and grades."
        )
    },
    {
        "tags": ["student access", "login", "account required", "solve quiz"],
        "q": "Can students access quizzes without an account?",
        "a": (
            "No. Students must **sign up / log in** first. After logging in, they can enter a quiz code and submit."
        )
    },
    {
        "tags": ["quiz code", "share code", "where is code"],
        "q": "Where do I find the quiz code?",
        "a": (
            "In the quiz card on your dashboard, you’ll see **Code:** (example: ABC123). Share this code with students."
        )
    },
]

def _normalize(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text

def _best_answer(message: str) -> str:
    msg = _normalize(message)

    # 1) quick tag hit (high precision)
    for item in TEACHER_KB:
        for t in item["tags"]:
            if _normalize(t) in msg:
                return item["a"]

    # 2) fuzzy match against known questions + tags (handles different wording)
    candidates = []
    for item in TEACHER_KB:
        candidates.append(item["q"])
        candidates.extend(item["tags"])

    best = difflib.get_close_matches(msg, [_normalize(c) for c in candidates], n=1, cutoff=0.55)
    if best:
        best_norm = best[0]
        for item in TEACHER_KB:
            if _normalize(item["q"]) == best_norm:
                return item["a"]
            for t in item["tags"]:
                if _normalize(t) == best_norm:
                    return item["a"]

    # fallback
    return (
        "I can help with:\n"
        "• Creating subject folders\n"
        "• Moving quizzes into folders\n"
        "• Exporting submissions to Excel\n"
        "• Student login/access\n\n"
        "Try asking: **How do I move a quiz into a folder?**"
    )

@staff_required
@require_POST
def teacher_help_bot(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        data = {}

    message = (data.get("message") or "").strip()
    if not message:
        return JsonResponse({"reply": "Type your question and I’ll help."})

    reply = _best_answer(message)
    return JsonResponse({"reply": reply})


@student_required
def enter_quiz(request):
    form = EnterQuizForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        quiz_code = form.cleaned_data["quiz_code"].strip().upper()

        quiz = Quiz.objects.filter(code=quiz_code).first()
        if not quiz:
            messages.error(request, "Invalid quiz code.")
            return render(request, "quizzes/enter_quiz.html", {"form": form})

        return redirect("take_quiz", quiz_code=quiz_code)

    return render(request, "quizzes/enter_quiz.html", {"form": form})



@student_required
def take_quiz(request, quiz_code):
    quiz = get_object_or_404(Quiz, code=quiz_code.upper())
    questions = quiz.questions.all().order_by("id")

    sp = request.user.student_profile
    student_name = f"{sp.first_name} {sp.second_name} {sp.third_name}"

    if request.method == "POST":
        total = questions.count()
        score = 0

        submission = Submission.objects.create(
            quiz=quiz,
            student_user=request.user,
            student_name=student_name,
            score=0,
            total=total,
        )

        for q in questions:
            selected = request.POST.get(f"question_{q.id}")  # "1" / "2" / ...
            selected_int = int(selected) if selected else None

            is_correct = (selected_int == q.correct_option)
            if is_correct:
                score += 1

            Answer.objects.create(
                submission=submission,
                question=q,
                selected=selected_int,
                is_correct=is_correct,
            )

        submission.score = score
        submission.save()

        return redirect("quiz_result", quiz_code=quiz.code, submission_id=submission.id)

    # ✅ GET request: show quiz page (solve here)
    return render(request, "quizzes/take_quiz.html", {
        "quiz": quiz,
        "questions": questions,
    })

@student_required
def quiz_result(request, quiz_code, submission_id):
    quiz = get_object_or_404(Quiz, code=quiz_code.upper())

    submission = get_object_or_404(
        Submission,
        id=submission_id,
        quiz=quiz,
        student_user=request.user,  # 🔥 prevents other students viewing it
    )

    answers = submission.answers.select_related("question").all().order_by("question__id")

    return render(request, "quizzes/quiz_result.html", {
        "quiz": quiz,
        "submission": submission,
        "answers": answers
    })


def teacher_signup(request):
    if request.user.is_authenticated:
        return redirect("teacher_quizzes")
    form=TeacherSignupForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        user=form.save(commit=False)
        user.set_password(form.cleaned_data['password1'])
        user.is_staff=True
        user.save()
        
        login(request,user)
        messages.success(request,"Account created successfully.")
        return redirect("teacher_quizzes")
    return render(request,"quizzes/teacher_signup.html",{'form':form})

def teacher_login(request):
    if request.user.is_authenticated:
        # if already logged-in teacher, go dashboard; if student, kick them to student dashboard
        if request.user.is_staff:
            return redirect("teacher_quizzes")
        return redirect("student_dashboard")

    form = TeacherLoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )
        if user and user.is_staff:
            login(request, user)
            return redirect("teacher_quizzes")
        messages.error(request, "Invalid teacher credentials.")

    return render(request, "quizzes/teacher_login.html", {"form": form})

@staff_required
def teacher_quizzes(request):
    folders = SubjectFolder.objects.filter(teacher=request.user).order_by("name")
    ungrouped = Quiz.objects.filter(teacher=request.user, folder__isnull=True).order_by("-created_at")
    return render(request, "quizzes/teacher_folders.html", {
        "folders": folders,
        "ungrouped": ungrouped,
    })
@staff_required
def export_submissions_excel(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, teacher=request.user)

    submissions = (
        Submission.objects
        .filter(quiz=quiz)
        .select_related("student_user", "quiz")
        .order_by("-submitted_at")
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Submissions"

    headers = [
        "Quiz Title",
        "Quiz Code",
        "Submitted At",
        "Student Full Name",
        "University ID",
        "Section",
        "City",
        "Major",
        "Score",
        "Total",
        "Percentage",
    ]
    ws.append(headers)

    for s in submissions:
        # defaults for guest submissions
        full_name = s.student_name
        university_id = ""
        section = ""
        city = ""
        major = ""

        # if student account exists, pull profile data
        if s.student_user and hasattr(s.student_user, "student_profile"):
            sp = s.student_user.student_profile
            full_name = f"{sp.first_name} {sp.second_name} {sp.third_name}"
            university_id = sp.university_id
            section = sp.section
            city = sp.city
            major = sp.get_major_display()

        percent = round((s.score / s.total) * 100, 2) if s.total else 0

        ws.append([
            quiz.title,
            quiz.code,
            s.submitted_at.strftime("%Y-%m-%d %H:%M"),
            full_name,
            university_id,
            section,
            city,
            major,
            s.score,
            s.total,
            f"{percent}%",
        ])

    # (nice) auto-size columns
    for col_idx, header in enumerate(headers, start=1):
        col_letter = get_column_letter(col_idx)
        max_len = len(header)
        for cell in ws[col_letter]:
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max_len + 2, 40)

    # return as downloadable file
    filename = f"{quiz.code}_submissions.xlsx"
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response

    
@staff_required
def create_folder(request):
    form = FolderForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        folder = form.save(commit=False)
        folder.teacher = request.user
        folder.save()
        messages.success(request, "Folder created.")
        return redirect("teacher_quizzes")
    return render(request, "quizzes/create_folder.html", {"form": form})

@staff_required
def folder_detail(request, folder_id):
    folder = get_object_or_404(SubjectFolder, id=folder_id, teacher=request.user)
    quizzes = folder.quizzes.all().order_by("-created_at")
    return render(request, "quizzes/folder_detail.html", {
        "folder": folder,
        "quizzes": quizzes,
    })

@staff_required
def export_folder_submissions_excel(request, folder_id):
    folder = get_object_or_404(SubjectFolder, id=folder_id, teacher=request.user)

    quizzes = folder.quizzes.all()
    submissions = (
        Submission.objects
        .filter(quiz__in=quizzes)
        .select_related("quiz", "student_user")
        .order_by("quiz__title", "-submitted_at")
    )

    from django.http import HttpResponse
    from openpyxl import Workbook
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = f"{folder.name} Submissions"[:31]

    headers = [
        "Subject Folder",
        "Quiz Title",
        "Quiz Code",
        "Submitted At",
        "Student Full Name",
        "University ID",
        "Section",
        "City",
        "Major",
        "Score",
        "Total",
        "Percentage",
    ]
    ws.append(headers)

    for s in submissions:
        full_name = s.student_name
        university_id = ""
        section = ""
        city = ""
        major = ""

        if s.student_user and hasattr(s.student_user, "student_profile"):
            sp = s.student_user.student_profile
            full_name = f"{sp.first_name} {sp.second_name} {sp.third_name}"
            university_id = sp.university_id
            section = sp.section
            city = sp.city
            major = sp.get_major_display()

        percent = round((s.score / s.total) * 100, 2) if s.total else 0

        ws.append([
            folder.name,
            s.quiz.title,
            s.quiz.code,
            s.submitted_at.strftime("%Y-%m-%d %H:%M"),
            full_name,
            university_id,
            section,
            city,
            major,
            s.score,
            s.total,
            f"{percent}%",
        ])

    for col_idx, header in enumerate(headers, start=1):
        col_letter = get_column_letter(col_idx)
        max_len = len(header)
        for cell in ws[col_letter]:
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max_len + 2, 40)

    filename = f"{folder.name}_submissions.xlsx".replace(" ", "_")
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response

@staff_required
def create_quiz(request):
    pre_folder_id = request.GET.get("folder")

    form = QuizForm(request.POST or None, teacher=request.user)

    # Preselect folder when opening the page
    if request.method == "GET" and pre_folder_id:
        form.initial["folder"] = pre_folder_id

    if request.method == "POST" and form.is_valid():
        quiz = form.save(commit=False)
        quiz.teacher = request.user
        quiz.save()
        messages.success(request, f"Quiz created. Code: {quiz.code}")

        # if created inside a folder, go back to that folder
        if quiz.folder_id:
            return redirect("folder_detail", quiz.folder_id)

        return redirect("teacher_quizzes")

    return render(request, "quizzes/create_quiz.html", {"form": form})


@staff_required
def create_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, teacher=request.user)
    form = QuestionForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        q = form.save(commit=False)
        q.quiz = quiz
        q.save()
        messages.success(request, "Question added.")
        return redirect("teacher_quizzes")

    return render(request, "quizzes/create_question.html", {"quiz": quiz, "form": form})


@staff_required
def quiz_submissions(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, teacher=request.user)
    submissions = quiz.submissions.all().order_by("-submitted_at")
    return render(request, "quizzes/quiz_submissions.html", {
        "quiz": quiz,
        "submissions": submissions
    })

@staff_required
def delete_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, teacher=request.user)

    if request.method == "POST":
        quiz.delete()
        messages.success(request, "Quiz deleted.")
        return redirect("teacher_quizzes")

    return render(request, "quizzes/confirm_delete.html", {"quiz": quiz})


def teacher_logout(request):
    logout(request)
    return redirect('teacher_login')

def student_signup(request):
    if request.user.is_authenticated:
        return redirect("enter_quiz")

    form = StudentSignupForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.set_password(form.cleaned_data["password1"])
        user.is_staff = False
        user.save()

        StudentProfile.objects.create(
            user=user,
            first_name=form.cleaned_data["first_name"],
            second_name=form.cleaned_data["second_name"],
            third_name=form.cleaned_data["third_name"],
            university_id=form.cleaned_data["university_id"],
            city=form.cleaned_data["city"],
            section=form.cleaned_data["section"],
            major=form.cleaned_data["major"],
        )

        login(request, user)
        messages.success(request, "Student account created successfully.")
        return redirect("enter_quiz")

    return render(request, "quizzes/student_signup.html", {"form": form})


def student_login(request):
    if request.user.is_authenticated:
        return redirect("student_dashboard")

    form = StudentLoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )

        if user is not None and not user.is_staff:
            login(request, user)
            return redirect("student_dashboard")

        messages.error(request, "Invalid username or password.")

    return render(request, "quizzes/student_login.html", {"form": form})

@student_required
def student_dashboard(request):
    profile = request.user.student_profile

    # show history
    submissions = (
        Submission.objects
        .filter(student_user=request.user)
        .select_related("quiz")
        .order_by("-submitted_at")
    )

    # quiz code form on dashboard
    form = EnterQuizForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        quiz_code = form.cleaned_data["quiz_code"].strip().upper()
        quiz = Quiz.objects.filter(code=quiz_code).first()
        if not quiz:
            messages.error(request, "Invalid quiz code.")
        else:
            return redirect("take_quiz", quiz_code=quiz.code)

    return render(request, "quizzes/student_dashboard.html", {
        "profile": profile,
        "submissions": submissions,
        "form": form,
    })

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import Submission

@student_required
def student_submission_detail(request, submission_id):
    submission = get_object_or_404(
        Submission.objects.select_related("quiz", "student_user").prefetch_related("answers__question"),
        id=submission_id,
        student_user=request.user,  
    )

    answers = submission.answers.select_related("question").all().order_by("question__id")

    return render(request, "quizzes/student_submission_detail.html", {
        "submission": submission,
        "quiz": submission.quiz,
        "answers": answers,
    })



def app_logout(request):
    logout(request)
    return redirect("home")

@staff_required
def move_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, teacher=request.user)
    form = MoveQuizForm(request.POST or None, teacher=request.user)

    if request.method == "POST" and form.is_valid():
        quiz.folder = form.cleaned_data["folder"]
        quiz.save()
        messages.success(request, "Quiz moved successfully.")
        return redirect("teacher_quizzes")

    return render(request, "quizzes/move_quiz.html", {
        "quiz": quiz,
        "form": form
    })

# Create your views here.
