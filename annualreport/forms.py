from django import forms
from .models import Achievement, AchievementLink

class AchievementForm(forms.ModelForm):
    """
    Form for creating and editing achievements
    """
    
    # Additional field for links (multiple URLs)
    links = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'أضف روابط المحتوى أو الملفات (رابط واحد في كل سطر)',
            'class': 'form-control'
        }),
        label='روابط المحتوى أو الملفات',
        help_text='يمكنك إضافة أكثر من رابط، رابط واحد في كل سطر'
    )
    
    class Meta:
        model = Achievement
        fields = [
            'section',
            'title',
            'description',
            'achievement_date',
            'display_in_report',
        ]
        widgets = {
            'section': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل عنوان الإنجاز',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'اكتب تفاصيل الإنجاز',
                'required': True
            }),
            'achievement_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'اختر تاريخ الإنجاز'
            }),
            'display_in_report': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'section': 'القسم الخاص بالإنجاز *',
            'title': 'عنوان الإنجاز *',
            'description': 'تفاصيل الإنجاز *',
            'achievement_date': 'تاريخ الإنجاز',
            'display_in_report': 'عرض الإنجاز في التقرير السنوي',
        }
    
    def __init__(self, *args, **kwargs):
        self.instance_pk = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)
        
        # If editing an existing achievement, populate the links field
        if self.instance.pk:
            existing_links = self.instance.links.all()
            if existing_links:
                links_text = '\n'.join([link.link_url for link in existing_links])
                self.initial['links'] = links_text
    
    def clean_links(self):
        """
        Validate and clean the links field
        """
        links_text = self.cleaned_data.get('links', '')
        
        if not links_text:
            return []
        
        # Split by newlines and filter empty lines
        links = [link.strip() for link in links_text.split('\n') if link.strip()]
        
        # Validate each URL
        validated_links = []
        for link in links:
            # Basic URL validation
            if not link.startswith(('http://', 'https://')):
                link = 'https://' + link
            validated_links.append(link)
        
        return validated_links
    
    def save(self, commit=True):
        """
        Save the achievement and its links
        """
        achievement = super().save(commit=False)
        
        if commit:
            achievement.save()
            
            # Handle links
            links_data = self.cleaned_data.get('links', [])
            
            # Delete existing links
            achievement.links.all().delete()
            
            # Create new links
            for link_url in links_data:
                AchievementLink.objects.create(
                    achievement=achievement,
                    link_url=link_url
                )
        
        return achievement