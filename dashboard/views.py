from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
    context = {
        'user': request.user,
        'total_incidents': 0,  # Will be updated in later phases
        'active_incidents': 0,
        'resolved_incidents': 0,
    }
    return render(request, 'dashboard/dashboard.html', context)