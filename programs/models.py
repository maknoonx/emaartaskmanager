# programs/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator

Employee = get_user_model()

class Program(models.Model):
    """
    Program model representing a housing program
    """
    name = models.CharField(
        max_length=200,
        verbose_name="اسم البرنامج",
        help_text="اسم البرنامج"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="وصف البرنامج",
        help_text="وصف تفصيلي للبرنامج"
    )
    
    number_of_houses = models.PositiveIntegerField(
        verbose_name="عدد المنازل",
        help_text="عدد المنازل في البرنامج",
        validators=[MinValueValidator(1)]
    )
    
    address = models.TextField(
        verbose_name="العنوان",
        help_text="عنوان البرنامج"
    )
    
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='created_programs',
        verbose_name="منشئ البرنامج"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاريخ التحديث"
    )
    
    class Meta:
        verbose_name = "برنامج"
        verbose_name_plural = "البرامج"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('programs:detail', kwargs={'pk': self.pk})


class House(models.Model):
    """
    House model representing individual houses in a program
    """
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name='houses',
        verbose_name="البرنامج"
    )
    
    house_number = models.PositiveIntegerField(
        verbose_name="رقم المنزل",
        help_text="رقم المنزل في البرنامج"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء"
    )
    
    class Meta:
        verbose_name = "منزل"
        verbose_name_plural = "المنازل"
        ordering = ['house_number']
        unique_together = ['program', 'house_number']
    
    def __str__(self):
        return f"منزل رقم {self.house_number} - {self.program.name}"
    
    def get_absolute_url(self):
        return reverse('programs:house_detail', kwargs={'program_pk': self.program.pk, 'house_pk': self.pk})


class HouseGeneralInfo(models.Model):
    """
    General information about a house
    """
    BUILDING_TYPE_CHOICES = [
        ('popular', 'شعبي'),
        ('reinforced', 'مسلح'),
    ]
    
    house = models.OneToOneField(
        House,
        on_delete=models.CASCADE,
        related_name='general_info',
        verbose_name="المنزل"
    )
    
    owner_name = models.CharField(
        max_length=200,
        verbose_name="اسم صاحب المنزل"
    )
    
    id_number = models.CharField(
        max_length=20,
        verbose_name="رقم الهوية"
    )
    
    number_of_residents = models.PositiveIntegerField(
        verbose_name="عدد الأفراد"
    )
    
    phone_number = models.CharField(
        max_length=20,
        verbose_name="رقم الجوال"
    )
    
    neighborhood = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="الحي"
    )
    
    building_type = models.CharField(
        max_length=20,
        choices=BUILDING_TYPE_CHOICES,
        verbose_name="نوع المبنى"
    )
    
    # Room counts
    bedrooms = models.PositiveIntegerField(
        verbose_name="عدد غرف النوم",
        validators=[MinValueValidator(1), MaxValueValidator(8)]
    )
    
    bathrooms = models.PositiveIntegerField(
        verbose_name="عدد دورات المياه",
        validators=[MinValueValidator(1), MaxValueValidator(8)]
    )
    
    living_rooms = models.PositiveIntegerField(
        verbose_name="عدد غرف المعيشة",
        validators=[MinValueValidator(1), MaxValueValidator(8)]
    )
    
    kitchens = models.PositiveIntegerField(
        verbose_name="عدد المطابخ",
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    majlis = models.PositiveIntegerField(
        verbose_name="عدد المجالس",
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    rooftops = models.PositiveIntegerField(
        verbose_name="عدد الأسطح",
        validators=[MinValueValidator(0), MaxValueValidator(3)],
        default=0
    )
    
    courtyards = models.PositiveIntegerField(
        verbose_name="عدد الأحواش",
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        default=0
    )
    
    plot_area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="مساحة القطعة",
        help_text="بالمتر المربع"
    )
    
    house_area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="مساحة المنزل",
        help_text="بالمتر المربع"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاريخ التحديث"
    )
    
    class Meta:
        verbose_name = "معلومات عامة للمنزل"
        verbose_name_plural = "معلومات عامة للمنازل"
    
    def __str__(self):
        return f"معلومات عامة - {self.house}"


class RoomDetail(models.Model):
    """
    Detailed information about individual rooms
    """
    ROOM_TYPE_CHOICES = [
        ('bedroom', 'غرفة نوم'),
        ('bathroom', 'دورة مياه'),
        ('living_room', 'غرفة معيشة'),
        ('kitchen', 'مطبخ'),
        ('majlis', 'مجلس'),
        ('rooftop', 'سطح'),
        ('courtyard', 'حوش'),
    ]
    
    FURNITURE_CONDITION_CHOICES = [
        ('excellent', 'ممتاز'),
        ('needs_change', 'تغيير'),
    ]
    
    WINDOW_CONDITION_CHOICES = [
        ('excellent', 'ممتازة'),
        ('maintenance', 'صيانة'),
        ('needs_change', 'تغيير'),
        ('none', 'لا يوجد'),
    ]
    
    DOOR_CONDITION_CHOICES = [
        ('excellent', 'ممتازة'),
        ('maintenance', 'صيانة'),
        ('needs_change', 'تغيير'),
    ]
    
    CEILING_TYPE_CHOICES = [
        ('wood', 'خشب'),
        ('zinc', 'زنك'),
        ('reinforced', 'مسلح'),
        ('mixed', 'منوع'),
        ('open', 'مفتوح'),
    ]
    
    CONDITION_CHOICES = [
        ('excellent', 'ممتازة'),
        ('maintenance', 'صيانة'),
        ('needs_change', 'تغيير'),
    ]
    
    INSULATION_CHOICES = [
        ('excellent', 'ممتازة'),
        ('needs_insulation', 'يحتاج عزل'),
    ]
    
    GYPSUM_CHOICES = [
        ('excellent', 'ممتازة'),
        ('maintenance', 'صيانة'),
        ('iron', 'حديد'),
    ]
    
    PAINT_CHOICES = [
        ('excellent', 'ممتاز'),
        ('maintenance', 'صيانة'),
        ('treatment', 'معالجة'),
    ]
    
    WALL_CHOICES = [
        ('excellent', 'ممتازة'),
        ('maintenance', 'صيانة'),
        ('treatment', 'معالجة'),
    ]
    
    FLOOR_TYPE_CHOICES = [
        ('concrete', 'صبة'),
        ('tiles', 'بلاط'),
    ]
    
    FLOOR_CONDITION_CHOICES = [
        ('excellent', 'ممتازة'),
        ('maintenance', 'صيانة'),
        ('needs_change', 'تغيير'),
    ]
    
    LEVEL_CONDITION_CHOICES = [
        ('normal', 'عادية'),
        ('medium', 'متوسطة'),
        ('large', 'كبيرة'),
    ]
    
    AC_TYPE_CHOICES = [
        ('split', 'سبلت'),
        ('window', 'شباك'),
    ]
    
    ELECTRICAL_VOLTAGE_CHOICES = [
        ('excellent', 'ممتاز'),
        ('needs_conversion', 'يجب التحويل'),
    ]
    
    ELECTRICAL_EXTENSION_CHOICES = [
        ('excellent', 'ممتازة'),
        ('external', 'خارجي'),
        ('partial', 'جزئي'),
    ]
    
    PLUMBING_CHOICES = [
        ('internal', 'داخلي'),
        ('external', 'خارجي'),
        ('partial', 'جزئي'),
    ]
    
    YES_NO_CHOICES = [
        ('yes', 'نعم'),
        ('no', 'لا'),
    ]
    
    HEATER_CONDITION_CHOICES = [
        ('excellent', 'ممتاز'),
        ('maintenance', 'صيانة'),
        ('needs_change', 'تغيير'),
    ]
    
    EXTRACTOR_CHOICES = [
        ('exists', 'يوجد'),
        ('none', 'لا يوجد'),
        ('needs_central', 'بحاجة لمركزي'),
    ]
    
    TANK_CHOICES = [
        ('yes', 'نعم'),
        ('no', 'لا'),
        ('external', 'خارجي'),
    ]
    
    KITCHEN_CONDITION_CHOICES = [
        ('excellent', 'ممتازة'),
        ('maintenance', 'صيانة'),
        ('new', 'جديد'),
    ]
    
    COURTYARD_FLOOR_CHOICES = [
        ('concrete', 'صبة'),
        ('flooring', 'أرضيات'),
        ('gravel', 'بحص'),
    ]
    
    COURTYARD_WALL_CHOICES = [
        ('excellent', 'ممتازة'),
        ('needs_change', 'تغيير'),
        ('humidity', 'رطوبة'),
    ]
    
    EXTERIOR_PAINT_CHOICES = [
        ('excellent', 'ممتاز'),
        ('treated', 'معالج'),
        ('iron', 'حديد'),
    ]
    
    house = models.ForeignKey(
        House,
        on_delete=models.CASCADE,
        related_name='room_details',
        verbose_name="المنزل"
    )
    
    room_type = models.CharField(
        max_length=20,
        choices=ROOM_TYPE_CHOICES,
        verbose_name="نوع الغرفة"
    )
    
    room_number = models.PositiveIntegerField(
        verbose_name="رقم الغرفة",
        help_text="رقم الغرفة من نفس النوع"
    )
    
    # Common fields for all room types
    area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="المساحة م²",
        null=True,
        blank=True
    )
    
    # Fields for bedrooms, living rooms, majlis, kitchens, bathrooms
    people_count = models.PositiveIntegerField(
        verbose_name="كم شخص فيها",
        null=True,
        blank=True
    )
    
    furniture_condition = models.CharField(
        max_length=20,
        choices=FURNITURE_CONDITION_CHOICES,
        verbose_name="حالة الأثاث",
        null=True,
        blank=True
    )
    
    windows_count = models.PositiveIntegerField(
        verbose_name="عدد الشبابيك",
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True,
        blank=True
    )
    
    doors_count = models.PositiveIntegerField(
        verbose_name="عدد الأبواب",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    
    windows_condition = models.CharField(
        max_length=20,
        choices=WINDOW_CONDITION_CHOICES,
        verbose_name="حالة الشبابيك",
        null=True,
        blank=True
    )
    
    doors_condition = models.CharField(
        max_length=20,
        choices=DOOR_CONDITION_CHOICES,
        verbose_name="حالة الأبواب",
        null=True,
        blank=True
    )
    
    ceiling_type = models.CharField(
        max_length=20,
        choices=CEILING_TYPE_CHOICES,
        verbose_name="نوع السقف",
        null=True,
        blank=True
    )
    
    ceiling_condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        verbose_name="حالة الأسقف",
        null=True,
        blank=True
    )
    
    insulation_condition = models.CharField(
        max_length=20,
        choices=INSULATION_CHOICES,
        verbose_name="حالة العزل",
        null=True,
        blank=True
    )
    
    gypsum_condition = models.CharField(
        max_length=20,
        choices=GYPSUM_CHOICES,
        verbose_name="حالة الجبس",
        null=True,
        blank=True
    )
    
    paint_condition = models.CharField(
        max_length=20,
        choices=PAINT_CHOICES,
        verbose_name="حالة الدهان",
        null=True,
        blank=True
    )
    
    wall_condition = models.CharField(
        max_length=20,
        choices=WALL_CHOICES,
        verbose_name="حالة الجدران",
        null=True,
        blank=True
    )
    
    floor_type = models.CharField(
        max_length=20,
        choices=FLOOR_TYPE_CHOICES,
        verbose_name="نوع الأرضيات",
        null=True,
        blank=True
    )
    
    floor_condition = models.CharField(
        max_length=20,
        choices=FLOOR_CONDITION_CHOICES,
        verbose_name="حالة الأرضيات",
        null=True,
        blank=True
    )
    
    level_condition = models.CharField(
        max_length=20,
        choices=LEVEL_CONDITION_CHOICES,
        verbose_name="حالة المناسيب",
        null=True,
        blank=True
    )
    
    # Structural problems - multiple choice
    structural_problems = models.JSONField(
        verbose_name="مشاكل إنشائية",
        default=list,
        blank=True,
        help_text="رطوبة، كراك عادي، كراك متوسط، كراك خطير، لا يوجد كراك"
    )
    
    ac_count = models.PositiveIntegerField(
        verbose_name="عدد المكيفات",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    
    ac_type = models.CharField(
        max_length=20,
        choices=AC_TYPE_CHOICES,
        verbose_name="نوع التكييف",
        null=True,
        blank=True
    )
    
    ac_condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        verbose_name="حالة التكييف",
        null=True,
        blank=True
    )
    
    electrical_voltage = models.CharField(
        max_length=20,
        choices=ELECTRICAL_VOLTAGE_CHOICES,
        verbose_name="حالة الجهد الكهربائي",
        null=True,
        blank=True
    )
    
    electrical_extensions = models.CharField(
        max_length=20,
        choices=ELECTRICAL_EXTENSION_CHOICES,
        verbose_name="التمديدات الكهربائية",
        null=True,
        blank=True
    )
    
    electrical_finishing = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        verbose_name="التشطيبات الكهربائية",
        null=True,
        blank=True
    )
    
    # Fields specific to bathrooms and kitchens
    plumbing_extensions = models.CharField(
        max_length=20,
        choices=PLUMBING_CHOICES,
        verbose_name="تمديد المواسير",
        null=True,
        blank=True
    )
    
    plumbing_finishing = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        verbose_name="حالة التشطيب",
        null=True,
        blank=True
    )
    
    # Fields specific to bathrooms
    bathroom_shortage = models.CharField(
        max_length=5,
        choices=YES_NO_CHOICES,
        verbose_name="هل يوجد قصور في دورات المياه",
        null=True,
        blank=True
    )
    
    heater_condition = models.CharField(
        max_length=20,
        choices=HEATER_CONDITION_CHOICES,
        verbose_name="حالة السخان",
        null=True,
        blank=True
    )
    
    extractor_condition = models.CharField(
        max_length=20,
        choices=EXTRACTOR_CHOICES,
        verbose_name="حالة الشفاط",
        null=True,
        blank=True
    )
    
    can_add_bathroom = models.CharField(
        max_length=5,
        choices=YES_NO_CHOICES,
        verbose_name="هل يمكن إضافة دورات مياه",
        null=True,
        blank=True
    )
    
    ground_tank = models.CharField(
        max_length=20,
        choices=TANK_CHOICES,
        verbose_name="هل يوجد خزان أرضي",
        null=True,
        blank=True
    )
    
    overhead_tank = models.CharField(
        max_length=5,
        choices=YES_NO_CHOICES,
        verbose_name="هل يوجد خزان علوي",
        null=True,
        blank=True
    )
    
    ground_tank_condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        verbose_name="حالة الخزان الأرضي",
        null=True,
        blank=True
    )
    
    overhead_tank_condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        verbose_name="حالة الخزان العلوي",
        null=True,
        blank=True
    )
    
    tank_accessories_condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        verbose_name="حالة مرافق الخزان",
        null=True,
        blank=True
    )
    
    appliances_condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        verbose_name="الأجهزة الكهربائية",
        null=True,
        blank=True
    )
    
    # Fields specific to kitchens
    kitchen_condition = models.CharField(
        max_length=20,
        choices=KITCHEN_CONDITION_CHOICES,
        verbose_name="حالة المطبخ",
        null=True,
        blank=True
    )
    
    # Fields specific to courtyards
    courtyard_floor_type = models.CharField(
        max_length=20,
        choices=COURTYARD_FLOOR_CHOICES,
        verbose_name="نوع الأرضيات",
        null=True,
        blank=True
    )
    
    courtyard_floor_condition = models.CharField(
        max_length=20,
        choices=FLOOR_CONDITION_CHOICES,
        verbose_name="حالة الأرضيات",
        null=True,
        blank=True
    )
    
    courtyard_wall_condition = models.CharField(
        max_length=20,
        choices=COURTYARD_WALL_CHOICES,
        verbose_name="حالة الجدران",
        null=True,
        blank=True
    )
    
    exterior_paint = models.CharField(
        max_length=20,
        choices=EXTERIOR_PAINT_CHOICES,
        verbose_name="الدهان الخارجي",
        null=True,
        blank=True
    )
    
    courtyard_area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="مساحة الحوش",
        null=True,
        blank=True
    )
    
    # Fields specific to rooftops
    rooftop_area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="مساحة السطح",
        null=True,
        blank=True
    )
    
    notes = models.TextField(
        verbose_name="ملاحظات",
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاريخ التحديث"
    )
    
    class Meta:
        verbose_name = "تفاصيل الغرفة"
        verbose_name_plural = "تفاصيل الغرف"
        unique_together = ['house', 'room_type', 'room_number']
        ordering = ['room_type', 'room_number']
    
    def __str__(self):
        return f"{self.get_room_type_display()} {self.room_number} - {self.house}"
    
    def get_absolute_url(self):
        return reverse('programs:room_detail', kwargs={
            'program_pk': self.house.program.pk,
            'house_pk': self.house.pk,
            'room_pk': self.pk
        })