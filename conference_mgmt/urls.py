from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render, redirect
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

@login_required
def homepage(request):
    from conference.models import Conference, UserConferenceRole
    from django.db.models import Q
    
    user = request.user
    
    # Only show conferences where user is chair, pc_member, or author
    user_conferences = Conference.objects.filter(
        Q(chair=user) |
        Q(userconferencerole__user=user, userconferencerole__role__in=['author', 'pc_member'])
    ).distinct().filter(is_approved=True)
    
    # Add role information to each conference
    for conference in user_conferences:
        conference.user_roles = UserConferenceRole.objects.filter(
            user=user, 
            conference=conference
        ).values_list('role', flat=True)
        if conference.chair == user and 'chair' not in conference.user_roles:
            conference.user_roles = list(conference.user_roles) + ['chair']
    
    context = {
        'user': user,
        'user_conferences': user_conferences,
    }
    return render(request, 'homepage.html', context)

def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('homepage')
    else:
        return render(request, 'landing.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('conference/', include('conference.urls', namespace='conference')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('', root_redirect, name='landing'),
    path('home/', homepage, name='homepage'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 