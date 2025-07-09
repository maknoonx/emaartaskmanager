# programs/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from .models import Program, House, HouseGeneralInfo, RoomDetail
from .forms import ProgramForm, HouseGeneralInfoForm, RoomDetailForm

@login_required
def index(request):
    """Display all programs with search and pagination"""
    programs = Program.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        programs = programs.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(address__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(programs, 12)  # 12 programs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': 'البرامج',
        'current_page': 'programs',
        'page_obj': page_obj,
        'search_query': search_query,
        'total_programs': programs.count()
    }
    
    return render(request, 'programs/index.html', context)


@login_required
def create_program(request):
    """Create a new program"""
    if request.method == 'POST':
        form = ProgramForm(request.POST)
        if form.is_valid():
            program = form.save(commit=False)
            program.created_by = request.user
            program.save()
            
            # Create houses for the program
            for i in range(1, program.number_of_houses + 1):
                House.objects.create(
                    program=program,
                    house_number=i
                )
            
            messages.success(request, f'تم إنشاء البرنامج "{program.name}" بنجاح مع {program.number_of_houses} منزل')
            return redirect('programs:detail', pk=program.pk)
    else:
        form = ProgramForm()
    
    context = {
        'title': 'إضافة برنامج جديد',
        'current_page': 'programs',
        'form': form
    }
    
    return render(request, 'programs/create.html', context)


@login_required
def program_detail(request, pk):
    """Display program details"""
    program = get_object_or_404(Program, pk=pk)
    houses = program.houses.all()
    
    context = {
        'title': f'برنامج: {program.name}',
        'current_page': 'programs',
        'program': program,
        'houses': houses
    }
    
    return render(request, 'programs/detail.html', context)


@login_required
def edit_program(request, pk):
    """Edit an existing program"""
    program = get_object_or_404(Program, pk=pk)
    
    if request.method == 'POST':
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            old_house_count = program.number_of_houses
            program = form.save()
            new_house_count = program.number_of_houses
            
            # Adjust house count if changed
            if new_house_count > old_house_count:
                # Add new houses
                for i in range(old_house_count + 1, new_house_count + 1):
                    House.objects.create(
                        program=program,
                        house_number=i
                    )
            elif new_house_count < old_house_count:
                # Remove excess houses (from the end)
                excess_houses = program.houses.filter(house_number__gt=new_house_count)
                excess_houses.delete()
            
            messages.success(request, f'تم تحديث البرنامج "{program.name}" بنجاح')
            return redirect('programs:detail', pk=program.pk)
    else:
        form = ProgramForm(instance=program)
    
    context = {
        'title': f'تعديل برنامج: {program.name}',
        'current_page': 'programs',
        'form': form,
        'program': program
    }
    
    return render(request, 'programs/edit.html', context)


@login_required
@require_http_methods(["DELETE", "POST"])
def delete_program(request, pk):
    """Delete a program with confirmation"""
    program = get_object_or_404(Program, pk=pk)
    
    try:
        program_name = program.name
        program.delete()
        
        success_msg = f'تم حذف البرنامج "{program_name}" بنجاح'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': success_msg})
        
        messages.success(request, success_msg)
        return redirect('programs:index')
        
    except Exception as e:
        error_msg = f'حدث خطأ أثناء حذف البرنامج: {str(e)}'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        messages.error(request, error_msg)
        return redirect('programs:index')


@login_required
def houses_list(request, program_pk):
    """Display houses in a program"""
    program = get_object_or_404(Program, pk=program_pk)
    houses = program.houses.all()
    
    context = {
        'title': f'منازل برنامج: {program.name}',
        'current_page': 'programs',
        'program': program,
        'houses': houses
    }
    
    return render(request, 'programs/houses_list.html', context)


@login_required
def house_detail(request, program_pk, house_pk):
    """Display house details and management buttons"""
    program = get_object_or_404(Program, pk=program_pk)
    house = get_object_or_404(House, pk=house_pk, program=program)
    
    # Check if general info exists
    try:
        general_info = house.general_info
        has_general_info = True
    except HouseGeneralInfo.DoesNotExist:
        general_info = None
        has_general_info = False
    
    context = {
        'title': f'منزل رقم {house.house_number} - {program.name}',
        'current_page': 'programs',
        'program': program,
        'house': house,
        'general_info': general_info,
        'has_general_info': has_general_info
    }
    
    return render(request, 'programs/house_detail.html', context)


@login_required
def house_general_info(request, program_pk, house_pk):
    """Create or edit house general information"""
    program = get_object_or_404(Program, pk=program_pk)
    house = get_object_or_404(House, pk=house_pk, program=program)
    
    try:
        general_info = house.general_info
        is_edit = True
    except HouseGeneralInfo.DoesNotExist:
        general_info = None
        is_edit = False
    
    if request.method == 'POST':
        if is_edit:
            form = HouseGeneralInfoForm(request.POST, instance=general_info)
        else:
            form = HouseGeneralInfoForm(request.POST)
        
        if form.is_valid():
            general_info = form.save(commit=False)
            general_info.house = house
            general_info.save()
            
            action = 'تحديث' if is_edit else 'إضافة'
            messages.success(request, f'تم {action} المعلومات العامة للمنزل بنجاح')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': f'تم {action} المعلومات بنجاح'})
            
            return redirect('programs:house_detail', program_pk=program.pk, house_pk=house.pk)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    else:
        if is_edit:
            form = HouseGeneralInfoForm(instance=general_info)
        else:
            form = HouseGeneralInfoForm()
    
    context = {
        'title': f'معلومات عامة - منزل رقم {house.house_number}',
        'current_page': 'programs',
        'program': program,
        'house': house,
        'form': form,
        'is_edit': is_edit
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'programs/partials/general_info_form.html', context)
    
    return render(request, 'programs/house_general_info.html', context)


@login_required
def edit_house_general_info(request, program_pk, house_pk):
    """Edit house general information (redirect to general_info view)"""
    return house_general_info(request, program_pk, house_pk)


@login_required
def technical_analysis(request, program_pk, house_pk):
    """Display technical analysis page with room cards"""
    program = get_object_or_404(Program, pk=program_pk)
    house = get_object_or_404(House, pk=house_pk, program=program)
    
    # Check if general info exists
    try:
        general_info = house.general_info
    except HouseGeneralInfo.DoesNotExist:
        messages.error(request, 'يجب إكمال المعلومات العامة للمنزل أولاً')
        return redirect('programs:house_detail', program_pk=program.pk, house_pk=house.pk)
    
    # Get existing room details for status checking
    existing_room_details = house.room_details.all()
    existing_rooms_dict = {}
    for room_detail in existing_room_details:
        key = f"{room_detail.room_type}_{room_detail.room_number}"
        existing_rooms_dict[key] = room_detail
    
    # Create room cards based on general info
    room_cards = []
    
    # Bedrooms
    for i in range(1, general_info.bedrooms + 1):
        key = f"bedroom_{i}"
        room_detail = existing_rooms_dict.get(key)
        room_cards.append({
            'type': 'bedroom',
            'type_display': 'غرفة نوم',
            'number': i,
            'icon': 'bx-bed',
            'has_details': room_detail is not None,
            'room_detail': room_detail
        })
    
    # Bathrooms
    for i in range(1, general_info.bathrooms + 1):
        key = f"bathroom_{i}"
        room_detail = existing_rooms_dict.get(key)
        room_cards.append({
            'type': 'bathroom',
            'type_display': 'دورة مياه',
            'number': i,
            'icon': 'bx-bath',
            'has_details': room_detail is not None,
            'room_detail': room_detail
        })
    
    # Living rooms
    for i in range(1, general_info.living_rooms + 1):
        key = f"living_room_{i}"
        room_detail = existing_rooms_dict.get(key)
        room_cards.append({
            'type': 'living_room',
            'type_display': 'غرفة معيشة',
            'number': i,
            'icon': 'bx-home',
            'has_details': room_detail is not None,
            'room_detail': room_detail
        })
    
    # Kitchens
    for i in range(1, general_info.kitchens + 1):
        key = f"kitchen_{i}"
        room_detail = existing_rooms_dict.get(key)
        room_cards.append({
            'type': 'kitchen',
            'type_display': 'مطبخ',
            'number': i,
            'icon': 'bx-restaurant',
            'has_details': room_detail is not None,
            'room_detail': room_detail
        })
    
    # Majlis
    for i in range(1, general_info.majlis + 1):
        key = f"majlis_{i}"
        room_detail = existing_rooms_dict.get(key)
        room_cards.append({
            'type': 'majlis',
            'type_display': 'مجلس',
            'number': i,
            'icon': 'bx-group',
            'has_details': room_detail is not None,
            'room_detail': room_detail
        })
    
    # Rooftops
    for i in range(1, general_info.rooftops + 1):
        key = f"rooftop_{i}"
        room_detail = existing_rooms_dict.get(key)
        room_cards.append({
            'type': 'rooftop',
            'type_display': 'سطح',
            'number': i,
            'icon': 'bx-building',
            'has_details': room_detail is not None,
            'room_detail': room_detail
        })
    
    # Courtyards
    for i in range(1, general_info.courtyards + 1):
        key = f"courtyard_{i}"
        room_detail = existing_rooms_dict.get(key)
        room_cards.append({
            'type': 'courtyard',
            'type_display': 'حوش',
            'number': i,
            'icon': 'bx-landscape',
            'has_details': room_detail is not None,
            'room_detail': room_detail
        })
    
    # Calculate progress statistics
    total_rooms = len(room_cards)
    analyzed_rooms = sum(1 for room in room_cards if room['has_details'])
    remaining_rooms = total_rooms - analyzed_rooms
    progress_percentage = round((analyzed_rooms / total_rooms * 100) if total_rooms > 0 else 0)
    
    context = {
        'title': f'التحليل الفني - منزل رقم {house.house_number}',
        'current_page': 'programs',
        'program': program,
        'house': house,
        'general_info': general_info,
        'room_cards': room_cards,
        'total_rooms': total_rooms,
        'analyzed_rooms': analyzed_rooms,
        'remaining_rooms': remaining_rooms,
        'progress_percentage': progress_percentage
    }
    
    return render(request, 'programs/technical_analysis.html', context)


@login_required
def room_detail(request, program_pk, house_pk, room_type, room_number):
    """Display room details and form"""
    program = get_object_or_404(Program, pk=program_pk)
    house = get_object_or_404(House, pk=house_pk, program=program)
    
    # Get or create room detail
    try:
        room_detail = RoomDetail.objects.get(
            house=house,
            room_type=room_type,
            room_number=room_number
        )
        is_edit = True
    except RoomDetail.DoesNotExist:
        room_detail = None
        is_edit = False
    
    room_type_display = dict(RoomDetail.ROOM_TYPE_CHOICES).get(room_type, room_type)
    
    context = {
        'title': f'{room_type_display} {room_number} - منزل رقم {house.house_number}',
        'current_page': 'programs',
        'program': program,
        'house': house,
        'room_detail': room_detail,
        'room_type': room_type,
        'room_number': room_number,
        'room_type_display': room_type_display,
        'is_edit': is_edit
    }
    
    return render(request, 'programs/room_detail.html', context)


@login_required
def edit_room_detail(request, program_pk, house_pk, room_type, room_number):
    """Edit room technical details"""
    program = get_object_or_404(Program, pk=program_pk)
    house = get_object_or_404(House, pk=house_pk, program=program)
    
    # Get or create room detail
    try:
        room_detail = RoomDetail.objects.get(
            house=house,
            room_type=room_type,
            room_number=room_number
        )
        is_edit = True
    except RoomDetail.DoesNotExist:
        room_detail = None
        is_edit = False
    
    if request.method == 'POST':
        if is_edit:
            form = RoomDetailForm(request.POST, instance=room_detail, room_type=room_type)
        else:
            form = RoomDetailForm(request.POST, room_type=room_type)
        
        if form.is_valid():
            room_detail = form.save(commit=False)
            room_detail.house = house
            room_detail.room_type = room_type
            room_detail.room_number = room_number
            room_detail.save()
            
            action = 'تحديث' if is_edit else 'إضافة'
            room_type_display = dict(RoomDetail.ROOM_TYPE_CHOICES).get(room_type, room_type)
            messages.success(request, f'تم {action} تفاصيل {room_type_display} {room_number} بنجاح')
            
            return redirect('programs:room_detail', 
                          program_pk=program.pk, 
                          house_pk=house.pk, 
                          room_type=room_type, 
                          room_number=room_number)
    else:
        if is_edit:
            form = RoomDetailForm(instance=room_detail, room_type=room_type)
        else:
            form = RoomDetailForm(room_type=room_type)
    
    room_type_display = dict(RoomDetail.ROOM_TYPE_CHOICES).get(room_type, room_type)
    
    context = {
        'title': f'تفاصيل {room_type_display} {room_number} - منزل رقم {house.house_number}',
        'current_page': 'programs',
        'program': program,
        'house': house,
        'form': form,
        'room_type': room_type,
        'room_number': room_number,
        'room_type_display': room_type_display,
        'is_edit': is_edit
    }
    
    return render(request, 'programs/edit_room_detail.html', context)