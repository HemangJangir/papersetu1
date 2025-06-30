from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from conference.models import Conference, ReviewerPool, ReviewInvite, UserConferenceRole, Paper, Review, User, Notification
from django.db.models import Count, Q
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.contrib import messages

@login_required
def dashboard(request):
    user = request.user
    # Determine roles
    roles = UserConferenceRole.objects.filter(user=user).values_list('role', flat=True).distinct()
    is_chair = 'chair' in roles
    is_author = 'author' in roles
    
    # Check if user is a reviewer (has reviewer profile or pending invitations)
    has_reviewer_profile = hasattr(user, 'reviewer_profile')
    has_pending_invites = ReviewInvite.objects.filter(reviewer=user, status='pending').exists()
    has_accepted_invites = ReviewInvite.objects.filter(reviewer=user, status='accepted').exists()
    is_reviewer = 'reviewer' in roles or has_reviewer_profile or has_pending_invites or has_accepted_invites

    # Get notifications
    notifications = Notification.objects.filter(recipient=user, is_read=False)[:10]

    # Chair context
    chaired_confs = Conference.objects.filter(chair=user)
    for conf in chaired_confs:
        conf.invite_url = request.build_absolute_uri(f"/conference/join/{conf.invite_link}/")
    chair_notifications = ReviewInvite.objects.filter(conference__chair=user, status='pending')

    # Author context
    search_query = request.GET.get('search', '')
    live_upcoming_confs = Conference.objects.filter(status__in=['live', 'upcoming'])
    if search_query:
        live_upcoming_confs = live_upcoming_confs.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )
    joined_confs = Conference.objects.filter(userconferencerole__user=user, userconferencerole__role='author')
    submitted_papers = Paper.objects.filter(author=user)

    # Reviewer context
    reviewer_invites = ReviewInvite.objects.filter(reviewer=user, status='pending')
    reviewing_confs = Conference.objects.filter(review_invites__reviewer=user, review_invites__status='accepted').distinct()
    
    # Get papers specifically assigned to this reviewer (papers with Review objects created for this reviewer)
    assigned_papers = Paper.objects.filter(reviews__reviewer=user)
    reviewer_notifications = reviewer_invites
    
    # Get papers that have been assigned to this reviewer but haven't been reviewed yet
    assigned_paper_ids = []
    for conf in reviewing_confs:
        # Get papers in this conference that have been assigned to this reviewer
        conf_papers = conf.papers.filter(reviews__reviewer=user)
        for paper in conf_papers:
            # Check if reviewer has already submitted a review for this paper
            if not Review.objects.filter(paper=paper, reviewer=user, decision__in=['accept', 'reject']).exists():
                assigned_paper_ids.append(paper.id)
    
    pending_paper_reviews = Paper.objects.filter(id__in=assigned_paper_ids)
    
    # Get review statistics for each paper
    paper_review_stats = {}
    for paper in pending_paper_reviews:
        total_reviews = paper.reviews.filter(decision__in=['accept', 'reject']).count()
        accept_count = paper.reviews.filter(decision='accept').count()
        reject_count = paper.reviews.filter(decision='reject').count()
        paper_review_stats[paper.id] = {
            'total_reviews': total_reviews,
            'accept_count': accept_count,
            'reject_count': reject_count,
            'needs_more_reviews': total_reviews < 2,
            'can_be_accepted': accept_count >= 2,
            'can_be_rejected': reject_count > accept_count and total_reviews >= 2
        }

    # All reviewers for modal assignment
    all_reviewers = User.objects.filter(reviewer_profile__isnull=False)

    # For dashboard toggle UI
    dashboard_view = request.GET.get('view', 'chair' if is_chair else 'author' if is_author else 'reviewer')
    
    # Handle success messages
    success_message = request.GET.get('message', '')

    # Get review statistics for all papers
    all_papers_review_stats = {}
    for paper in Paper.objects.all():
        total_reviews = paper.reviews.filter(decision__in=['accept', 'reject']).count()
        accept_count = paper.reviews.filter(decision='accept').count()
        reject_count = paper.reviews.filter(decision='reject').count()
        all_papers_review_stats[paper.id] = {
            'total_reviews': total_reviews,
            'accept_count': accept_count,
            'reject_count': reject_count,
        }

    if is_chair:
        all_chaired_papers = Paper.objects.filter(conference__in=chaired_confs)
    else:
        all_chaired_papers = Paper.objects.none()

    context = {
        'roles': roles,
        'dashboard_view': dashboard_view,
        'is_chair': is_chair,
        'is_author': is_author,
        'is_reviewer': is_reviewer,
        'chaired_confs': chaired_confs,
        'chair_notifications': chair_notifications,
        'joined_confs': joined_confs,
        'submitted_papers': submitted_papers,
        'reviewing_confs': reviewing_confs,
        'assigned_papers': assigned_papers,
        'reviewer_invites': reviewer_invites,
        'live_upcoming_confs': live_upcoming_confs,
        'search_query': search_query,
        'pending_paper_reviews': pending_paper_reviews,
        'all_reviewers': all_reviewers,
        'notifications': notifications,
        'success_message': success_message,
        'paper_review_stats': paper_review_stats,
        'all_papers_review_stats': all_papers_review_stats,
        'all_chaired_papers': all_chaired_papers,
    }
    return render(request, 'dashboard/dashboard.html', context)

@require_POST
@login_required
def review_invite_respond(request, invite_id):
    invite = get_object_or_404(ReviewInvite, id=invite_id, reviewer=request.user)
    response = request.POST.get('response')
    if response == 'accept':
        invite.status = 'accepted'
        invite.save()
        UserConferenceRole.objects.get_or_create(user=request.user, conference=invite.conference, role='reviewer')
        
        # Create notification for chair
        Notification.objects.create(
            recipient=invite.conference.chair,
            notification_type='reviewer_response',
            title=f'Reviewer Accepted Invitation',
            message=f'{request.user.get_full_name()} ({request.user.username}) has accepted the reviewer invitation for {invite.conference.name}.',
            related_conference=invite.conference,
            related_review_invite=invite
        )
        
    elif response == 'decline':
        invite.status = 'declined'
        invite.save()
        
        # Create notification for chair
        Notification.objects.create(
            recipient=invite.conference.chair,
            notification_type='reviewer_response',
            title=f'Reviewer Declined Invitation',
            message=f'{request.user.get_full_name()} ({request.user.username}) has declined the reviewer invitation for {invite.conference.name}.',
            related_conference=invite.conference,
            related_review_invite=invite
        )
    
    return HttpResponseRedirect(reverse('dashboard:dashboard') + '?view=reviewer')

@login_required
def review_paper(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id)
    print(f"DEBUG: Review paper view accessed for paper {paper_id} by user {request.user.username}")
    
    # Check if user is an accepted reviewer for this conference
    is_accepted_reviewer = ReviewInvite.objects.filter(conference=paper.conference, reviewer=request.user, status='accepted').exists()
    print(f"DEBUG: User {request.user.username} is accepted reviewer: {is_accepted_reviewer}")
    
    if not is_accepted_reviewer:
        print(f"DEBUG: Redirecting - user not an accepted reviewer")
        return redirect('dashboard:dashboard')
    
    # Check if user has already submitted a review with a decision
    existing_review = Review.objects.filter(paper=paper, reviewer=request.user, decision__in=['accept', 'reject']).first()
    print(f"DEBUG: Existing review for user {request.user.username}: {existing_review}")
    
    if existing_review:
        print(f"DEBUG: Redirecting - user already submitted a review")
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        decision = request.POST.get('decision')
        if decision in ['accept', 'reject']:
            # Use update_or_create to avoid unique constraint errors
            review, created = Review.objects.update_or_create(
                paper=paper,
                reviewer=request.user,
                defaults={'decision': decision}
            )
            
            # Update paper status based on all reviews
            paper.update_status_based_on_reviews()
            
            # Create notification for author
            Notification.objects.create(
                recipient=paper.author,
                notification_type='paper_review',
                title=f'Paper Review Completed',
                message=f'Your paper "{paper.title}" has been reviewed by {request.user.get_full_name() or request.user.username}. Decision: {decision.title()}.',
                related_paper=paper,
                related_conference=paper.conference,
                related_review=review
            )
            
            # Create notification for chair about the review
            Notification.objects.create(
                recipient=paper.conference.chair,
                notification_type='paper_review',
                title=f'Review Submitted',
                message=f'{request.user.get_full_name() or request.user.username} has submitted a review for paper "{paper.title}". Decision: {decision.title()}.',
                related_paper=paper,
                related_conference=paper.conference,
                related_review=review
            )
            
            print(f"DEBUG: Review submitted successfully - {decision}")
            return redirect(f'/dashboard/?view=reviewer&message=review_submitted')
    
    context = {
        'paper': paper,
        'conference': paper.conference,
        'author': paper.author,
    }
    return render(request, 'dashboard/review_paper.html', context)

@login_required
def chair_conference_detail(request, conf_id):
    conference = get_object_or_404(Conference, id=conf_id)
    # Ensure only the chair can access
    if conference.chair != request.user:
        return redirect('dashboard:dashboard')
    
    papers = Paper.objects.filter(conference=conference).select_related('author')
    authors = UserConferenceRole.objects.filter(conference=conference, role='author').select_related('user')
    reviewers = UserConferenceRole.objects.filter(conference=conference, role='reviewer').select_related('user')
    review_invites = ReviewInvite.objects.filter(conference=conference)
    
    # Get all available reviewers (those who have volunteered)
    available_reviewers = User.objects.filter(reviewer_profile__isnull=False).exclude(
        review_invites__conference=conference
    )
    
    # Search functionality for reviewers
    search_query = request.GET.get('search', '')
    if search_query:
        available_reviewers = available_reviewers.filter(
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query) | 
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    assign_message = ''
    invite_message = ''
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'assign_paper':
            paper_id = request.POST.get('paper_id')
            reviewer_username = request.POST.get('reviewer_username')
            try:
                paper = Paper.objects.get(id=paper_id, conference=conference)
                reviewer = User.objects.get(username=reviewer_username)
                # Only assign if reviewer is accepted for this conference
                if ReviewInvite.objects.filter(conference=conference, reviewer=reviewer, status='accepted').exists():
                    # Create or get Review object to assign the paper to reviewer
                    review, created = Review.objects.get_or_create(
                        paper=paper,
                        reviewer=reviewer,
                        defaults={'decision': None}  # None means not reviewed yet
                    )
                    
                    if created:
                        assign_message = f"Assigned {reviewer.username} to paper '{paper.title}'."
                    else:
                        assign_message = f"{reviewer.username} was already assigned to paper '{paper.title}'."
                    
                    # Create notification for reviewer
                    Notification.objects.create(
                        recipient=reviewer,
                        notification_type='paper_assignment',
                        title=f'Paper Assignment',
                        message=f'You have been assigned to review the paper "{paper.title}" for {conference.name}.',
                        related_paper=paper,
                        related_conference=conference
                    )
                else:
                    assign_message = f"User {reviewer_username} is not an accepted reviewer for this conference."
            except (Paper.DoesNotExist, User.DoesNotExist):
                assign_message = "Invalid paper or reviewer."
        
        elif action == 'invite_reviewer':
            reviewer_username = request.POST.get('reviewer_username')
            try:
                reviewer = User.objects.get(username=reviewer_username)
                # Check if already invited
                if not ReviewInvite.objects.filter(conference=conference, reviewer=reviewer).exists():
                    invite = ReviewInvite.objects.create(conference=conference, reviewer=reviewer)
                    invite_message = f"Invitation sent to {reviewer.username}."
                    
                    # Create notification for reviewer
                    Notification.objects.create(
                        recipient=reviewer,
                        notification_type='reviewer_invite',
                        title=f'Reviewer Invitation',
                        message=f'You have been invited to review papers for {conference.name}. Please check your dashboard to accept or decline.',
                        related_conference=conference,
                        related_review_invite=invite
                    )
                    
                    # Debug: Print invitation details
                    print(f"DEBUG: Created invitation for {reviewer.username} to {conference.name}")
                    print(f"DEBUG: Invitation ID: {invite.id}, Status: {invite.status}")
                else:
                    invite_message = f"{reviewer.username} has already been invited."
                    print(f"DEBUG: {reviewer.username} already invited to {conference.name}")
            except User.DoesNotExist:
                invite_message = "Invalid reviewer username."
                print(f"DEBUG: User {reviewer_username} not found")
    
    invite_url = request.build_absolute_uri(f"/conference/join/{conference.invite_link}/")
    
    context = {
        'conference': conference,
        'papers': papers,
        'authors': authors,
        'reviewers': reviewers,
        'review_invites': review_invites,
        'available_reviewers': available_reviewers,
        'assign_message': assign_message,
        'invite_message': invite_message,
        'invite_url': invite_url,
        'search_query': search_query,
    }
    return render(request, 'dashboard/chair_conference_detail.html', context)

@require_POST
@login_required
def paper_review_respond(request, review_id):
    review = get_object_or_404(Review, id=review_id, reviewer=request.user, decision__isnull=True)
    response = request.POST.get('response')
    if response == 'accept':
        # Reviewer accepts assignment, do nothing (keep Review object)
        pass
    elif response == 'decline':
        # Reviewer declines assignment, delete Review object
        review.delete()
    return HttpResponseRedirect(reverse('dashboard:dashboard') + '?view=reviewer')

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})

@require_POST
@login_required
def bulk_assign_papers(request):
    user = request.user
    # Check if user is a chair
    chaired_confs = Conference.objects.filter(chair=user)
    if not chaired_confs.exists():
        messages.error(request, 'You are not authorized to assign papers.')
        return redirect('dashboard:dashboard')
    
    paper_ids = request.POST.getlist('papers')
    reviewer_ids = request.POST.getlist('reviewers')
    
    if not paper_ids or not reviewer_ids:
        messages.error(request, 'Please select at least one paper and one reviewer.')
        return redirect('dashboard:dashboard')
    
    papers = Paper.objects.filter(id__in=paper_ids, conference__chair=user)
    reviewers = User.objects.filter(id__in=reviewer_ids)
    
    assigned_count = 0
    errors = []
    
    for paper in papers:
        for reviewer in reviewers:
            # Check if reviewer is accepted for this specific conference
            try:
                invite = ReviewInvite.objects.get(conference=paper.conference, reviewer=reviewer)
                if invite.status == 'accepted':
                    # Create Review object to assign the paper to reviewer
                    review, review_created = Review.objects.get_or_create(
                        paper=paper,
                        reviewer=reviewer,
                        defaults={'decision': None}  # None means not reviewed yet
                    )
                    
                    if review_created:
                        assigned_count += 1
                        # Notify reviewer
                        Notification.objects.create(
                            recipient=reviewer,
                            notification_type='paper_assignment',
                            title=f'Paper Assignment',
                            message=f'You have been assigned to review the paper "{paper.title}" for {paper.conference.name}.',
                            related_paper=paper,
                            related_conference=paper.conference
                        )
                    else:
                        errors.append(f"{reviewer.username} was already assigned to paper '{paper.title}'")
                else:
                    errors.append(f"{reviewer.username} has not accepted the invitation for {paper.conference.name}")
            except ReviewInvite.DoesNotExist:
                errors.append(f"{reviewer.username} has not been invited to {paper.conference.name}")
    
    if assigned_count > 0:
        messages.success(request, f'Successfully assigned {assigned_count} paper-reviewer pairs!')
    if errors:
        messages.warning(request, f'Some assignments failed: {", ".join(errors[:3])}{"..." if len(errors) > 3 else ""}')
    
    return redirect('dashboard:dashboard') 