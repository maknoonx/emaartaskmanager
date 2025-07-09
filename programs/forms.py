# programs/forms.py
from django import forms
from .models import Program, HouseGeneralInfo, RoomDetail

class ProgramForm(forms.ModelForm):
    """Form for creating and editing programs"""
    
    class Meta:
        model = Program
        fields = ['name', 'description', 'number_of_houses', 'address']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم البرنامج'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'وصف البرنامج'
            }),
            'number_of_houses': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'عدد المنازل'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'عنوان البرنامج'
            })
        }
        labels = {
            'name': 'اسم البرنامج *',
            'description': 'وصف البرنامج',
            'number_of_houses': 'عدد المنازل *',
            'address': 'العنوان *'
        }


class HouseGeneralInfoForm(forms.ModelForm):
    """Form for house general information"""
    
    class Meta:
        model = HouseGeneralInfo
        fields = [
            'owner_name', 'id_number', 'number_of_residents', 'phone_number',
            'neighborhood', 'building_type', 'bedrooms', 'bathrooms',
            'living_rooms', 'kitchens', 'majlis', 'rooftops', 'courtyards',
            'plot_area', 'house_area'
        ]
        widgets = {
            'owner_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم صاحب المنزل'
            }),
            'id_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الهوية'
            }),
            'number_of_residents': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'عدد الأفراد'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الجوال'
            }),
            'neighborhood': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الحي'
            }),
            'building_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'bedrooms': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 8
            }),
            'bathrooms': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 8
            }),
            'living_rooms': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 8
            }),
            'kitchens': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 5
            }),
            'majlis': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 5
            }),
            'rooftops': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 3
            }),
            'courtyards': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 4
            }),
            'plot_area': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'مساحة القطعة بالمتر المربع'
            }),
            'house_area': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'مساحة المنزل بالمتر المربع'
            })
        }
        labels = {
            'owner_name': 'اسم صاحب المنزل *',
            'id_number': 'رقم الهوية *',
            'number_of_residents': 'عدد الأفراد *',
            'phone_number': 'رقم الجوال *',
            'neighborhood': 'الحي',
            'building_type': 'نوع المبنى',
            'bedrooms': 'عدد غرف النوم (1-8)',
            'bathrooms': 'عدد دورات المياه (1-8)',
            'living_rooms': 'عدد غرف المعيشة (1-8)',
            'kitchens': 'عدد المطابخ (1-5)',
            'majlis': 'عدد المجالس (1-5)',
            'rooftops': 'عدد الأسطح (0-3)',
            'courtyards': 'عدد الأحواش (0-4)',
            'plot_area': 'مساحة القطعة (م²)',
            'house_area': 'مساحة المنزل (م²)'
        }


class RoomDetailForm(forms.ModelForm):
    """Form for room technical details"""
    
    # Structural problems choices
    STRUCTURAL_PROBLEMS_CHOICES = [
        ('humidity', 'رطوبة'),
        ('normal_crack', 'كراك عادي'),
        ('medium_crack', 'كراك متوسط'),
        ('dangerous_crack', 'كراك خطير'),
        ('no_crack', 'لا يوجد كراك'),
    ]
    
    structural_problems = forms.MultipleChoiceField(
        choices=STRUCTURAL_PROBLEMS_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=False,
        label='مشاكل إنشائية'
    )
    
    class Meta:
        model = RoomDetail
        fields = [
            'area', 'people_count', 'furniture_condition', 'windows_count',
            'doors_count', 'windows_condition', 'doors_condition', 'ceiling_type',
            'ceiling_condition', 'insulation_condition', 'gypsum_condition',
            'paint_condition', 'wall_condition', 'floor_type', 'floor_condition',
            'level_condition', 'structural_problems', 'ac_count', 'ac_type',
            'ac_condition', 'electrical_voltage', 'electrical_extensions',
            'electrical_finishing', 'plumbing_extensions', 'plumbing_finishing',
            'bathroom_shortage', 'heater_condition', 'extractor_condition',
            'can_add_bathroom', 'ground_tank', 'overhead_tank', 'ground_tank_condition',
            'overhead_tank_condition', 'tank_accessories_condition', 'appliances_condition',
            'kitchen_condition', 'courtyard_floor_type', 'courtyard_floor_condition',
            'courtyard_wall_condition', 'exterior_paint', 'courtyard_area',
            'rooftop_area', 'notes'
        ]
        widgets = {
            'area': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'المساحة بالمتر المربع'
            }),
            'people_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': 'عدد الأشخاص'
            }),
            'furniture_condition': forms.Select(attrs={
                'class': 'form-select'
            }),
            'windows_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10
            }),
            'doors_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 5
            }),
            'windows_condition': forms.Select(attrs={
                'class': 'form-select'
            }),
            'doors_condition': forms.Select(attrs={
                'class': 'form-select'
            }),
            'ceiling_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'ceiling_condition': forms.Select(attrs={
                'class': 'form-select'
            }),
            'insulation_condition': forms.Select(attrs={
                'class': 'form-select'
            }),
            'gypsum_condition': forms.Select(attrs={
                'class': 'form-select'
            }),
            'paint_condition': forms.Select(attrs={
                'class': 'form-select'
            }),
            'wall_condition': forms.Select(attrs={
                'class': 'form-select'
            }),
            'floor_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'floor_condition': forms.Select(attrs={
                'class': 'form-select'
            }),
            'level_condition': forms.Select(attrs={
                'class': 'form-select'
            }),
            'ac_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 5
            }),
            'ac_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'ac_condition': forms.Select(attrs={
                'class': 'form-select'
            }),
            'electrical_voltage': forms.Select(attrs={
                'class': 'form-select'
            }),
            'electrical_extensions': forms.Select(attrs={
                'class': 'form-select'
            }),
            'electrical_finishing': forms.Select(attrs={
                'class': 'form-select'
            }),
            'plumbing_extensions': forms.Select(attrs={
                'class': 'form-select'
            }),
            'plumbing_finishing': forms.Select(attrs={
                'class': 'form-select'
            }),
            'bathroom_shortage': forms.Select(attrs={
                'class': 'form-select'
            }),
            'heater_condition': forms.Select(attrs={
                'class': 'form-select'
            }),
            'extractor_condition': forms.Select(attrs={
                'class': 'form-select'
            }),
            'can_add_bathroom': forms.Select(attrs={
                'class': 'form-select'
            }),
            'ground_tank': forms.Select(attrs={
                'class': 'form-select'
            }),
            'overhead_tank': forms.Select(attrs={
                'class': 'form-select'
            }),
            'ground_tank_condition': forms.Select(attrs={
                'class': 'form-select'
            }),
            'overhead_tank_condition': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tank_accessories_condition': forms.Select(attrs={
                'class': 'form-select'
            }),
            'appliances_condition': forms.Select(attrs={
                'class': 'form-select'
            }),
            'kitchen_condition': forms.Select(attrs={
                'class': 'form-select'
            }),
            'courtyard_floor_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'courtyard_floor_condition': forms.Select(attrs={
                'class': 'form-select'
            }),
            'courtyard_wall_condition': forms.Select(attrs={
                'class': 'form-select'
            }),
            'exterior_paint': forms.Select(attrs={
                'class': 'form-select'
            }),
            'courtyard_area': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'مساحة الحوش بالمتر المربع'
            }),
            'rooftop_area': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'مساحة السطح بالمتر المربع'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'ملاحظات إضافية'
            })
        }
    
    def clean_structural_problems(self):
        """Convert structural problems list to JSON format"""
        problems = self.cleaned_data.get('structural_problems', [])
        return problems
    
    def __init__(self, *args, **kwargs):
        room_type = kwargs.pop('room_type', None)
        super().__init__(*args, **kwargs)
        
        # Set initial structural problems if instance exists
        if self.instance and self.instance.pk:
            self.initial['structural_problems'] = self.instance.structural_problems
        
        # Hide fields based on room type
        if room_type:
            self._customize_fields_for_room_type(room_type)
    
    def _customize_fields_for_room_type(self, room_type):
        """Customize form fields based on room type"""
        
        # Common fields for all room types
        common_fields = ['area']
        
        # Fields for rooms (bedrooms, living rooms, majlis)
        room_fields = [
            'people_count', 'furniture_condition', 'windows_count', 'doors_count',
            'windows_condition', 'doors_condition', 'ceiling_type', 'ceiling_condition',
            'insulation_condition', 'gypsum_condition', 'paint_condition', 'wall_condition',
            'floor_type', 'floor_condition', 'level_condition', 'structural_problems',
            'ac_count', 'ac_type', 'ac_condition', 'electrical_voltage',
            'electrical_extensions', 'electrical_finishing'
        ]
        
        # Fields for bathrooms
        bathroom_fields = room_fields + [
            'plumbing_extensions', 'plumbing_finishing', 'bathroom_shortage',
            'heater_condition', 'extractor_condition', 'can_add_bathroom',
            'ground_tank', 'overhead_tank', 'ground_tank_condition',
            'overhead_tank_condition', 'tank_accessories_condition', 'appliances_condition'
        ]
        
        # Fields for kitchens
        kitchen_fields = room_fields + [
            'plumbing_extensions', 'plumbing_finishing', 'appliances_condition',
            'kitchen_condition'
        ]
        
        # Fields for courtyards
        courtyard_fields = [
            'courtyard_area', 'electrical_voltage', 'electrical_extensions',
            'electrical_finishing', 'courtyard_floor_type', 'courtyard_floor_condition',
            'courtyard_wall_condition', 'exterior_paint'
        ]
        
        # Fields for rooftops
        rooftop_fields = ['rooftop_area', 'notes']
        
        # Determine which fields to show
        if room_type == 'bathroom':
            allowed_fields = bathroom_fields
        elif room_type == 'kitchen':
            allowed_fields = kitchen_fields
        elif room_type == 'courtyard':
            allowed_fields = courtyard_fields
        elif room_type == 'rooftop':
            allowed_fields = rooftop_fields
        else:  # bedroom, living_room, majlis
            allowed_fields = room_fields
        
        # Remove fields that shouldn't be shown for this room type
        fields_to_remove = []
        for field_name in self.fields:
            if field_name not in allowed_fields:
                fields_to_remove.append(field_name)
        
        for field_name in fields_to_remove:
            del self.fields[field_name]