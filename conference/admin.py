from django.contrib import admin
from .models import Conference, ReviewerPool, ReviewInvite, UserConferenceRole, Paper, Review

admin.site.register(Conference)
admin.site.register(ReviewerPool)
admin.site.register(ReviewInvite)
admin.site.register(UserConferenceRole)
admin.site.register(Paper)
admin.site.register(Review) 