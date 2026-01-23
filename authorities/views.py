from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from issues.models import Issue, IssueUpdate
from .models import Authority


@login_required
def dashboard(request):
    """Authority dashboard showing assigned issues"""
    # Get authorities this user is authorized for
    user_authorities = Authority.objects.filter(authorized_users=request.user)
    
    if not user_authorities.exists():
        messages.warning(request, "You are not authorized to manage any authorities.")
        return redirect('issues:home')
    
    # Get issues assigned to any of these authorities
    issues = Issue.objects.filter(assigned_authority__in=user_authorities).order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status', '')
    if status_filter:
        issues = issues.filter(status=status_filter)
    
    context = {
        'issues': issues,
        'user_authorities': user_authorities,
        'status_filter': status_filter,
    }
    return render(request, 'authorities/dashboard.html', context)


@login_required
def issue_detail(request, issue_id):
    """Authority view of a specific issue"""
    issue = get_object_or_404(Issue, id=issue_id)
    
    # Check if user is authorized for this issue's authority
    if not issue.assigned_authority or issue.assigned_authority not in Authority.objects.filter(authorized_users=request.user):
        messages.error(request, "You are not authorized to view this issue.")
        return redirect('authorities:dashboard')
    
    updates = IssueUpdate.objects.filter(issue=issue).order_by('-created_at')
    
    context = {
        'issue': issue,
        'updates': updates,
    }
    return render(request, 'authorities/issue_detail.html', context)


@login_required
def post_update(request, issue_id):
    """Post a status update for an issue"""
    issue = get_object_or_404(Issue, id=issue_id)
    
    # Check authorization
    if not issue.assigned_authority or issue.assigned_authority not in Authority.objects.filter(authorized_users=request.user):
        messages.error(request, "You are not authorized to update this issue.")
        return redirect('authorities:dashboard')
    
    if request.method == 'POST':
        status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if status:
            # Update issue status
            issue.status = status
            issue.save()
            
            # Create update record
            IssueUpdate.objects.create(
                issue=issue,
                author=request.user,
                status=status,
                notes=notes
            )
            
            messages.success(request, "Status update posted successfully.")
            return redirect('authorities:issue_detail', issue_id=issue.id)
    
    return redirect('authorities:issue_detail', issue_id=issue.id)
