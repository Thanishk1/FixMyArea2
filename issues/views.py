from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Issue, IssueCategory, IssueUpdate
from .utils import extract_gps_from_image, reverse_geocode
from authorities.services import find_authority_for_location


def home(request):
    """Home page with issue feed"""
    issues = Issue.objects.all().select_related('category', 'reporter', 'assigned_authority')
    
    # Filters
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '')
    
    if category_filter:
        issues = issues.filter(category_id=category_filter)
    
    if status_filter:
        issues = issues.filter(status=status_filter)
    
    if search_query:
        issues = issues.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location_text__icontains=search_query)
        )
    
    categories = IssueCategory.objects.all()
    
    context = {
        'issues': issues[:50],  # Limit to 50 most recent
        'categories': categories,
        'category_filter': int(category_filter) if category_filter else None,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'issues/home.html', context)


@login_required
def report_issue(request):
    """Report a new civic issue"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        image = request.FILES.get('image')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        location_text = request.POST.get('location_text', '')
        
        if not all([title, description, category_id, image]):
            messages.error(request, "Please fill in all required fields.")
            return redirect('issues:report')
        
        try:
            category = IssueCategory.objects.get(id=category_id)
        except IssueCategory.DoesNotExist:
            messages.error(request, "Invalid category selected.")
            return redirect('issues:report')
        
        # Try to extract GPS from image if not provided
        if not latitude or not longitude:
            lat, lng = extract_gps_from_image(image)
            if lat and lng:
                latitude = lat
                longitude = lng
                messages.info(request, "Location extracted from image EXIF data.")
        
        # If we have coordinates, try to get location text and assign authority
        assigned_authority = None
        if latitude and longitude:
            try:
                latitude = float(latitude)
                longitude = float(longitude)
                
                # Reverse geocode if location text not provided
                if not location_text:
                    location_text = reverse_geocode(latitude, longitude) or ''
                
                # Find authority for this location
                assigned_authority = find_authority_for_location(latitude, longitude)
                
                if assigned_authority:
                    messages.success(request, f"Issue assigned to {assigned_authority.name}.")
                else:
                    messages.warning(request, "No authority found for this location. Issue will be unassigned.")
            except (ValueError, TypeError):
                messages.warning(request, "Invalid coordinates provided.")
                latitude = None
                longitude = None
        
        # Create issue
        issue = Issue.objects.create(
            reporter=request.user,
            category=category,
            title=title,
            description=description,
            image=image,
            latitude=latitude,
            longitude=longitude,
            location_text=location_text,
            assigned_authority=assigned_authority,
        )
        
        messages.success(request, "Issue reported successfully!")
        return redirect('issues:detail', pk=issue.pk)
    
    categories = IssueCategory.objects.all()
    return render(request, 'issues/report.html', {'categories': categories})


def issue_detail(request, pk):
    """View details of a specific issue"""
    issue = get_object_or_404(Issue, pk=pk)
    updates = IssueUpdate.objects.filter(issue=issue).order_by('-created_at')
    
    context = {
        'issue': issue,
        'updates': updates,
    }
    return render(request, 'issues/detail.html', context)


def issues_by_category(request, category_id):
    """Filter issues by category"""
    category = get_object_or_404(IssueCategory, id=category_id)
    issues = Issue.objects.filter(category=category).order_by('-created_at')
    
    context = {
        'category': category,
        'issues': issues,
    }
    return render(request, 'issues/category.html', context)
