from django.urls import path
from . import views

urlpatterns = [
    path('', views.start_page, name='start_page'),
    path('home/', views.home, name='home'),
    path('quiz/', views.quiz, name='quiz'),
    path('api/get-quiz/', views.get_quiz, name='get_quiz'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('results/', views.results_page, name='results'),
    path('submit-quiz/', views.submit_quiz, name='submit_quiz'),
    path('reset-quiz/', views.reset_quiz, name='reset_quiz'),
    path('ai-quiz/', views.ai_quiz_view, name='ai_quiz'),
    path('ai-quiz/submit/', views.submit_ai_quiz, name='submit_ai_quiz'),
    path('', views.start_page, name='start_page'),

]