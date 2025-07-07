from django.db import models
from accounts.models import User

AREA_CHOICES = [
    ('AI', 'Artificial Intelligence'),
    ('ML', 'Machine Learning'),
    ('DS', 'Data Science'),
    ('CV', 'Computer Vision'),
    ('NLP', 'Natural Language Processing'),
    ('SE', 'Software Engineering'),
    ('CN', 'Computer Networks'),
    ('SEC', 'Cyber Security'),
    ('HCI', 'Human-Computer Interaction'),
    ('DB', 'Databases'),
    ('IOT', 'Internet of Things'),
    ('BIO', 'Bioinformatics'),
    ('EDU', 'Education Technology'),
    ('GRAPH', 'Computer Graphics'),
    ('OTHER', 'Other'),
]

class Conference(models.Model):
    name = models.CharField(max_length=255)
    acronym = models.CharField(max_length=50, blank=True)
    web_page = models.URLField(blank=True)
    venue = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    estimated_submissions = models.IntegerField(null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    primary_area = models.CharField(max_length=50, choices=AREA_CHOICES, default='AI')
    secondary_area = models.CharField(max_length=50, choices=AREA_CHOICES, default='AI')
    area_notes = models.TextField(blank=True)
    organizer = models.CharField(max_length=255, blank=True)
    organizer_web_page = models.URLField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=100, blank=True)
    is_approved = models.BooleanField(default=False)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requested_conferences', null=True, blank=True)
    description = models.TextField(blank=True)
    chair = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chaired_conferences')
    status = models.CharField(max_length=20, choices=[('upcoming', 'Upcoming'), ('live', 'Live'), ('completed', 'Completed')], default='upcoming')
    invite_link = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paper_submission_deadline = models.DateField(null=True, blank=True)
    paper_format = models.CharField(max_length=10, choices=[('pdf', 'PDF'), ('docx', 'DOCX')], default='pdf')

    def __str__(self):
        return self.name

class ReviewerPool(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='reviewer_profile')
    expertise = models.CharField(max_length=255)
    bio = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.expertise}"

class ReviewInvite(models.Model):
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name='review_invites')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_invites')
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('declined', 'Declined')], default='pending')
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invite: {self.reviewer} for {self.conference} ({self.status})"

class UserConferenceRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=[('chair', 'Chair'), ('author', 'Author'), ('reviewer', 'Reviewer')])
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'conference', 'role')

    def __str__(self):
        return f"{self.user} - {self.role} @ {self.conference}"

class Paper(models.Model):
    title = models.CharField(max_length=255)
    abstract = models.TextField()
    file = models.FileField(upload_to='papers/')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='papers')
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name='papers')
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('submitted', 'Submitted'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], default='submitted')

    def __str__(self):
        return self.title
    
    def update_status_based_on_reviews(self):
        """Update paper status based on review decisions"""
        reviews = self.reviews.filter(decision__in=['accept', 'reject'])
        
        if not reviews.exists():
            return  # No reviews yet
        
        accept_count = reviews.filter(decision='accept').count()
        reject_count = reviews.filter(decision='reject').count()
        total_reviews = reviews.count()
        
        # If at least 2 reviewers have accepted, accept the paper
        if accept_count >= 2:
            if self.status != 'accepted':
                self.status = 'accepted'
                self.save()
                
                # Create notification for author
                Notification.objects.create(
                    recipient=self.author,
                    notification_type='paper_decision',
                    title=f'Paper Accepted!',
                    message=f'Congratulations! Your paper "{self.title}" has been accepted for {self.conference.name} based on {accept_count} positive reviews.',
                    related_paper=self,
                    related_conference=self.conference
                )
                
                # Create notification for chair
                Notification.objects.create(
                    recipient=self.conference.chair,
                    notification_type='paper_decision',
                    title=f'Paper Auto-Accepted',
                    message=f'Paper "{self.title}" has been automatically accepted with {accept_count} positive reviews.',
                    related_paper=self,
                    related_conference=self.conference
                )
        # If majority of reviewers have rejected, reject the paper
        elif reject_count > accept_count and total_reviews >= 2:
            if self.status != 'rejected':
                self.status = 'rejected'
                self.save()
                
                # Create notification for author
                Notification.objects.create(
                    recipient=self.author,
                    notification_type='paper_decision',
                    title=f'Paper Decision',
                    message=f'Your paper "{self.title}" has been reviewed for {self.conference.name}. Status: Rejected (majority decision).',
                    related_paper=self,
                    related_conference=self.conference
                )
                
                # Create notification for chair
                Notification.objects.create(
                    recipient=self.conference.chair,
                    notification_type='paper_decision',
                    title=f'Paper Auto-Rejected',
                    message=f'Paper "{self.title}" has been automatically rejected with {reject_count} negative reviews.',
                    related_paper=self,
                    related_conference=self.conference
                )
        # If only 1 reviewer has reviewed and rejected, keep as submitted
        elif total_reviews == 1 and reject_count == 1:
            if self.status != 'submitted':
                self.status = 'submitted'
                self.save()

class Review(models.Model):
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    decision = models.CharField(max_length=10, choices=[('accept', 'Accept'), ('reject', 'Reject')], blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('paper', 'reviewer')

    def __str__(self):
        return f"{self.reviewer} review for {self.paper}: {self.decision}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('reviewer_invite', 'Reviewer Invitation'),
        ('reviewer_response', 'Reviewer Response'),
        ('paper_assignment', 'Paper Assignment'),
        ('paper_review', 'Paper Review'),
        ('paper_decision', 'Paper Decision'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    related_conference = models.ForeignKey(Conference, on_delete=models.CASCADE, null=True, blank=True)
    related_paper = models.ForeignKey(Paper, on_delete=models.CASCADE, null=True, blank=True)
    related_review_invite = models.ForeignKey(ReviewInvite, on_delete=models.CASCADE, null=True, blank=True)
    related_review = models.ForeignKey(Review, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.username} - {self.title}" 