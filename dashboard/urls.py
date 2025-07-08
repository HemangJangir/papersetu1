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
    path('pc/conference/<int:conf_id>/', views.pc_conference_detail, name='pc_conference_detail'),
    path('chair/conference/<int:conf_id>/pc/', views.pc_list, name='pc_list'),
    path('chair/conference/<int:conf_id>/pc/invite/', views.pc_invite, name='pc_invite'),
    path('chair/conference/<int:conf_id>/pc/invitations/', views.pc_invitations, name='pc_invitations'),
    path('chair/conference/<int:conf_id>/pc/remove/<int:user_id>/', views.pc_remove, name='pc_remove'),
    path('pc/invite/accept/<str:token>/', views.pc_invite_accept, name='pc_invite_accept'),
    path('conference/<int:conf_id>/submissions/', views.conference_submissions, name='conference_submissions'),
    path('conference/<int:conf_id>/administration/', views.conference_administration, name='conference_administration'),
    path('conference/<int:conf_id>/configuration/', views.conference_configuration, name='conference_configuration'),
    # Registration application URLs
    path('conference/<int:conf_id>/registration/apply/step1/', views.registration_application_step1, name='registration_application_step1'),
    path('conference/<int:conf_id>/registration/apply/step2/', views.registration_application_step2, name='registration_application_step2'),
    path('conference/<int:conf_id>/registration/confirmation/', views.registration_confirmation, name='registration_confirmation'),
    path('conference/<int:conf_id>/registration/status/', views.registration_status, name='registration_status'),
    # Analytics URLs
    path('conference/<int:conf_id>/analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('conference/<int:conf_id>/analytics/export/', views.analytics_export, name='analytics_export'),
    # Other Utilities URLs
    path('conference/<int:conf_id>/utilities/accepted-submissions/', views.accepted_submissions_list, name='accepted_submissions'),
    path('conference/<int:conf_id>/utilities/accepted-submissions/export/', views.export_accepted_submissions_csv, name='accepted_submissions_export'),
    path('conference/<int:conf_id>/utilities/reviews/', views.reviews_list, name='all_reviews'),
]
