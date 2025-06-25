from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from .forms import UserRegistrationForm
from .models import User
import random

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            otp = str(random.randint(100000, 999999))
            user.otp = otp
            user.otp_created_at = timezone.now()
            user.save()
            send_mail(
                'Your OTP for Conference Management Registration',
                f'Your OTP is: {otp}',
                'noreply@conference.com',
                [user.email],
                fail_silently=False,
            )
            request.session['pending_user_id'] = user.id
            return redirect('accounts:verify_otp')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def verify_otp(request):
    user_id = request.session.get('pending_user_id')
    if not user_id:
        return redirect('accounts:register')
    user = User.objects.get(id=user_id)
    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        if otp_input == user.otp:
            user.is_active = True
            user.is_verified = True
            user.otp = ''
            user.save()
            messages.success(request, 'Account verified! You can now log in.')
            return redirect('accounts:login')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
    return render(request, 'accounts/verify_otp.html')

from django.contrib.auth.views import LoginView

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    def get_success_url(self):
        return '/' 

def custom_logout(request):
    logout(request)
    return redirect('/') 