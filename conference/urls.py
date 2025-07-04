from django.urls import path
from . import views

app_name = 'conference'

urlpatterns = [
    path('create/', views.create_conference, name='create_conference'),
    path('reviewer-volunteer/', views.reviewer_volunteer, name='reviewer_volunteer'),
    path('<int:conference_id>/submit-paper/', views.submit_paper, name='submit_paper'),
    path('join/<str:invite_link>/', views.join_conference, name='join_conference'),
] 