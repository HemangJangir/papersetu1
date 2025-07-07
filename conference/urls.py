from django.urls import path
from . import views

app_name = 'conference'

urlpatterns = [
    path('', views.conferences_list, name='conferences_list'),
    path('create/', views.create_conference, name='create_conference'),
    path('reviewer-volunteer/', views.reviewer_volunteer, name='reviewer_volunteer'),
    path('<int:conference_id>/submit-paper/', views.submit_paper, name='submit_paper'),
    path('join/<str:invite_link>/', views.join_conference, name='join_conference'),
    path('<int:conference_id>/choose-role/', views.choose_conference_role, name='choose_conference_role'),
] 