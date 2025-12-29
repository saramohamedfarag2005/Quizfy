from django.urls import path 
from . import views

urlpatterns=[
    path("", views.home, name="home"),
    path("teacher/help-bot/", views.teacher_help_bot, name="teacher_help_bot"),


    path("quiz/<str:quiz_code>/",views.take_quiz,name="take_quiz"),
    path("quiz/<str:quiz_code>/result/<int:submission_id>/",views.quiz_result,name="quiz_result"),
    path("logout/", views.app_logout, name="app_logout"),
    
    path("teacher/signup/",views.teacher_signup,name="teacher_signup"),
    path("teacher/login/",views.teacher_login,name="teacher_login"),
    path("teacher/quizzes/",views.teacher_quizzes,name="teacher_quizzes"),
    path("teacher/quizzes/create/",views.create_quiz,name="create_quiz"),
    path("teacher/quizzes/<int:quiz_id>/questions/add/",views.create_question,name="create_question"),
    path("teacher/quizzes/<int:quiz_id>/submission/",views.quiz_submissions,name="quiz_submissions"),
    path("teacher/quizzes/<int:quiz_id>/delete/",views.delete_quiz,name="delete_quiz"),
    path("student/signup/", views.student_signup, name="student_signup"),
    path("student/login/", views.student_login, name="student_login"),
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("teacher/folders/create/", views.create_folder, name="create_folder"),
    path("teacher/folders/<int:folder_id>/", views.folder_detail, name="folder_detail"),
    path("teacher/folders/<int:folder_id>/export/", views.export_folder_submissions_excel, name="export_folder_submissions_excel"),
    path("teacher/quizzes/<int:quiz_id>/export/", views.export_submissions_excel, name="export_submissions_excel"),
    path("teacher/quizzes/<int:quiz_id>/move/", views.move_quiz, name="move_quiz"),
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("student/submissions/<int:submission_id>/", views.student_submission_detail, name="student_submission_detail"),





] 