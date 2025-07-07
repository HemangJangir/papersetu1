from django import forms
from .models import Conference, ReviewerPool, Paper, AREA_CHOICES

class ConferenceForm(forms.ModelForm):
    primary_area = forms.ChoiceField(choices=AREA_CHOICES)
    secondary_area = forms.ChoiceField(choices=AREA_CHOICES)
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    paper_submission_deadline = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    class Meta:
        model = Conference
        fields = [
            'name', 'acronym', 'web_page', 'venue', 'city', 'country',
            'estimated_submissions', 'start_date', 'end_date',
            'primary_area', 'secondary_area', 'area_notes',
            'organizer', 'organizer_web_page', 'contact_phone',
            'role', 'description', 'paper_submission_deadline', 'paper_format'
        ]

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