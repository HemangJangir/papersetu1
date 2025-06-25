from django import forms
from .models import Conference, ReviewerPool, Paper

class ConferenceForm(forms.ModelForm):
    class Meta:
        model = Conference
        fields = ['name', 'domain', 'description', 'start_date', 'end_date', 'paper_submission_deadline', 'paper_format', 'registration_fee']

class ReviewerVolunteerForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    class Meta:
        model = ReviewerPool
        fields = ['first_name', 'last_name', 'expertise', 'bio']

class PaperSubmissionForm(forms.ModelForm):
    class Meta:
        model = Paper
        fields = ['title', 'abstract', 'file'] 