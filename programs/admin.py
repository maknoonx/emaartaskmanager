# programs/admin.py
from django.contrib import admin
from .models import Program, House, HouseGeneralInfo, RoomDetail

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'number_of_houses', 'address', 'created_by', 'created_at')
    list_filter = ('created_at', 'created_by')
    search_fields = ('name', 'description', 'address')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('معلومات البرنامج', {
            'fields': ('name', 'description', 'number_of_houses', 'address')
        }),
        ('معلومات النظام', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'program', 'house_number', 'has_general_info', 'room_details_count')
    list_filter = ('program', 'created_at')
    search_fields = ('program__name', 'house_number')
    readonly_fields = ('created_at',)
    
    def has_general_info(self, obj):
        try:
            return bool(obj.general_info)
        except HouseGeneralInfo.DoesNotExist:
            return False
    has_general_info.boolean = True
    has_general_info.short_description = 'معلومات عامة'
    
    def room_details_count(self, obj):
        return obj.room_details.count()
    room_details_count.short_description = 'عدد الغرف المُحللة'


@admin.register(HouseGeneralInfo)
class HouseGeneralInfoAdmin(admin.ModelAdmin):
    list_display = ('house', 'owner_name', 'id_number', 'number_of_residents', 'building_type')
    list_filter = ('building_type', 'created_at')
    search_fields = ('owner_name', 'id_number', 'phone_number', 'house__program__name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('معلومات المالك', {
            'fields': ('house', 'owner_name', 'id_number', 'number_of_residents', 'phone_number', 'neighborhood')
        }),
        ('معلومات المبنى', {
            'fields': ('building_type', 'plot_area', 'house_area')
        }),
        ('توزيع الغرف', {
            'fields': ('bedrooms', 'bathrooms', 'living_rooms', 'kitchens', 'majlis', 'rooftops', 'courtyards')
        }),
        ('معلومات النظام', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(RoomDetail)
class RoomDetailAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'house', 'room_type', 'room_number', 'area', 'people_count')
    list_filter = ('room_type', 'furniture_condition', 'created_at', 'house__program')
    search_fields = ('house__program__name', 'house__house_number', 'room_type')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('معلومات الغرفة', {
            'fields': ('house', 'room_type', 'room_number', 'area', 'people_count')
        }),
        ('حالة الأثاث والتجهيزات', {
            'fields': ('furniture_condition', 'windows_count', 'doors_count', 'windows_condition', 'doors_condition'),
            'classes': ('collapse',)
        }),
        ('التفاصيل الإنشائية', {
            'fields': ('ceiling_type', 'ceiling_condition', 'wall_condition', 'floor_type', 'floor_condition', 'paint_condition', 'insulation_condition', 'gypsum_condition', 'level_condition', 'structural_problems'),
            'classes': ('collapse',)
        }),
        ('الكهرباء والتكييف', {
            'fields': ('electrical_voltage', 'electrical_extensions', 'electrical_finishing', 'ac_count', 'ac_type', 'ac_condition'),
            'classes': ('collapse',)
        }),
        ('السباكة والمياه', {
            'fields': ('plumbing_extensions', 'plumbing_finishing', 'bathroom_shortage', 'heater_condition', 'extractor_condition', 'can_add_bathroom', 'ground_tank', 'overhead_tank', 'ground_tank_condition', 'overhead_tank_condition', 'tank_accessories_condition', 'appliances_condition'),
            'classes': ('collapse',)
        }),
        ('تفاصيل خاصة', {
            'fields': ('kitchen_condition', 'courtyard_area', 'courtyard_floor_type', 'courtyard_floor_condition', 'courtyard_wall_condition', 'exterior_paint', 'rooftop_area', 'notes'),
            'classes': ('collapse',)
        }),
        ('معلومات النظام', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('house', 'house__program')