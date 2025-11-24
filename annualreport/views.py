from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from .models import Achievement, AchievementLink
from .forms import AchievementForm
import json

@login_required
def index(request):
    """
    Main page for Annual Report 2025
    Shows all achievements with filtering options
    """
    # Get filter parameter
    section_filter = request.GET.get('section', '')
    
    # Get all achievements that should be displayed
    achievements = Achievement.objects.filter(display_in_report=True)
    
    # Apply section filter if provided
    if section_filter:
        achievements = achievements.filter(section=section_filter)
    
    # Get statistics for each section
    section_stats = {}
    for section_code, section_name in Achievement.SECTION_CHOICES:
        count = Achievement.objects.filter(
            section=section_code,
            display_in_report=True
        ).count()
        section_stats[section_code] = {
            'name': section_name,
            'count': count
        }

    section_counts = {}
    for section_code, section_name in Achievement.SECTION_CHOICES:
        count = Achievement.objects.filter(section=section_code).count()
        section_counts[section_code] = count
    
    context = {
        'current_page': 'annual_report',
        'title': 'التقرير السنوي 2025',
        'achievements': achievements,
        'section_choices': Achievement.SECTION_CHOICES,
        'section_filter': section_filter,
        'section_stats': section_stats,
        'total_achievements': achievements.count(),
        'section_counts': section_counts,  # ✅ Add this
    }
    
    return render(request, 'annualreport/index.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def create_achievement(request):
    """
    Create a new achievement (AJAX)
    """
    if request.method == 'POST':
        form = AchievementForm(request.POST)
        
        if form.is_valid():
            achievement = form.save(commit=False)
            achievement.created_by = request.user
            achievement.save()
            form.save_m2m()  # Save links
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'تم إضافة الإنجاز بنجاح',
                    'achievement_id': achievement.pk
                })
            
            messages.success(request, 'تم إضافة الإنجاز بنجاح')
            return redirect('annualreport:index')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)
    else:
        form = AchievementForm()
    
    # Return form HTML for AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'annualreport/partials/achievement_form.html', {
            'form': form,
            'action': 'create',
            'modal_title': 'إضافة إنجاز جديد'
        })
    
    return render(request, 'annualreport/create.html', {
        'form': form,
        'current_page': 'annual_report'
    })


@login_required
@require_http_methods(["GET"])
def achievement_detail(request, pk):
    """
    View achievement details (AJAX)
    """
    achievement = get_object_or_404(Achievement, pk=pk)
    
    # Check if user can edit/delete
    can_edit = achievement.can_be_edited_by(request.user)
    can_delete = achievement.can_be_deleted_by(request.user)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'annualreport/partials/achievement_detail.html', {
            'achievement': achievement,
            'can_edit': can_edit,
            'can_delete': can_delete
        })
    
    return render(request, 'annualreport/detail.html', {
        'achievement': achievement,
        'can_edit': can_edit,
        'can_delete': can_delete,
        'current_page': 'annual_report'
    })


@login_required
@require_http_methods(["GET", "POST"])
def edit_achievement(request, pk):
    """
    Edit an existing achievement (AJAX)
    """
    achievement = get_object_or_404(Achievement, pk=pk)
    
    # Check permissions
    if not achievement.can_be_edited_by(request.user):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'ليس لديك صلاحية لتعديل هذا الإنجاز'
            }, status=403)
        
        messages.error(request, 'ليس لديك صلاحية لتعديل هذا الإنجاز')
        return redirect('annualreport:index')
    
    if request.method == 'POST':
        form = AchievementForm(request.POST, instance=achievement)
        
        if form.is_valid():
            form.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'تم تحديث الإنجاز بنجاح'
                })
            
            messages.success(request, 'تم تحديث الإنجاز بنجاح')
            return redirect('annualreport:index')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)
    else:
        form = AchievementForm(instance=achievement)
    
    # Return form HTML for AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'annualreport/partials/achievement_form.html', {
            'form': form,
            'achievement': achievement,
            'action': 'edit',
            'modal_title': 'تعديل الإنجاز'
        })
    
    return render(request, 'annualreport/edit.html', {
        'form': form,
        'achievement': achievement,
        'current_page': 'annual_report'
    })


@login_required
@require_http_methods(["POST"])
def delete_achievement(request, pk):
    """
    Delete an achievement (AJAX)
    """
    achievement = get_object_or_404(Achievement, pk=pk)
    
    # Check permissions
    if not achievement.can_be_deleted_by(request.user):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'ليس لديك صلاحية لحذف هذا الإنجاز'
            }, status=403)
        
        messages.error(request, 'ليس لديك صلاحية لحذف هذا الإنجاز')
        return redirect('annualreport:index')
    
    # Delete the achievement
    achievement_title = achievement.title
    achievement.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'تم حذف الإنجاز "{achievement_title}" بنجاح'
        })
    
    messages.success(request, f'تم حذف الإنجاز "{achievement_title}" بنجاح')
    return redirect('annualreport:index')


@login_required
@require_http_methods(["GET"])
def export_report(request):
    """
    Export annual report (future feature)
    """
    # This can be implemented later to export the report as PDF or other formats
    messages.info(request, 'ميزة التصدير قيد التطوير')
    return redirect('annualreport:index')