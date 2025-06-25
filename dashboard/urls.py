from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('review-invite/<int:invite_id>/respond/', views.review_invite_respond, name='review_invite_respond'),
    path('paper/<int:paper_id>/review/', views.review_paper, name='review_paper'),
    path('chair/conference/<int:conf_id>/', views.chair_conference_detail, name='chair_conference_detail'),
    path('paper-review/<int:review_id>/respond/', views.paper_review_respond, name='paper_review_respond'),
    path('notification/<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('chair/conference/<int:conf_id>/bulk-assign/', views.bulk_assign_papers, name='bulk_assign_papers'),
    path('bulk-assign/', views.bulk_assign_papers, name='bulk_assign_papers'),
] 