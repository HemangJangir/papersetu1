from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ConferenceForm, ReviewerVolunteerForm, PaperSubmissionForm
from .models import Conference, ReviewerPool, ReviewInvite, UserConferenceRole, Paper, Review
from accounts.models import User
from django.utils.crypto import get_random_string
from django.http import Http404

@login_required
def create_conference(request):
    if request.method == 'POST':
        form = ConferenceForm(request.POST)
        if form.is_valid():
            conference = form.save(commit=False)
            conference.chair = request.user
            conference.status = 'upcoming'
            conference.invite_link = get_random_string(32)
            conference.save()
            UserConferenceRole.objects.create(user=request.user, conference=conference, role='chair')
            messages.success(request, 'Conference created successfully!')
            return redirect('dashboard:dashboard')
        else:
            print('Conference form errors:', form.errors)
    else:
        form = ConferenceForm()
    return render(request, 'conference/create_conference.html', {'form': form})

@login_required
def reviewer_volunteer(request):
    if hasattr(request.user, 'reviewer_profile'):
        messages.info(request, 'You have already volunteered as a reviewer.')
        return redirect('dashboard:dashboard')
    if request.method == 'POST':
        form = ReviewerVolunteerForm(request.POST)
        if form.is_valid():
            reviewer = form.save(commit=False)
            reviewer.user = request.user
            # Save first and last name to user
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.save()
            reviewer.save()
            messages.success(request, 'Thank you for volunteering as a reviewer!')
            return redirect('dashboard:dashboard')
    else:
        form = ReviewerVolunteerForm()
    return render(request, 'conference/reviewer_volunteer.html', {'form': form})

@login_required
def submit_paper(request, conference_id):
    conference = get_object_or_404(Conference, id=conference_id)
    if request.method == 'POST':
        form = PaperSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            paper = form.save(commit=False)
            paper.author = request.user
            paper.conference = conference
            paper.save()
            UserConferenceRole.objects.get_or_create(user=request.user, conference=conference, role='author')
            messages.success(request, 'Paper submitted successfully!')
            return redirect('dashboard:dashboard')
    else:
        form = PaperSubmissionForm()
    return render(request, 'conference/submit_paper.html', {'form': form, 'conference': conference})

@login_required
def join_conference(request, invite_link):
    try:
        conference = Conference.objects.get(invite_link=invite_link)
    except Conference.DoesNotExist:
        raise Http404('Conference not found.')
    if request.method == 'POST':
        # Add user as author if not already
        UserConferenceRole.objects.get_or_create(user=request.user, conference=conference, role='author')
        messages.success(request, f'You have joined the conference "{conference.name}"!')
        return redirect('dashboard:dashboard')
    return render(request, 'conference/join_conference.html', {'conference': conference}) 