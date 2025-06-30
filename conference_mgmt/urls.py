from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

def homepage(request):
    return render(request, 'homepage.html', {'user': request.user})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('conference/', include('conference.urls', namespace='conference')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('', TemplateView.as_view(template_name='landing.html'), name='landing'),
    path('home/', homepage, name='homepage'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 