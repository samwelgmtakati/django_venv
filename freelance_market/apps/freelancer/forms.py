from django import forms
from django.forms import ModelForm
from .models import Freelancer, Skill
from django.utils.text import slugify

class SkillMultipleChoiceField(forms.ModelMultipleChoiceField):
    def clean(self, value):
        if value is not None:
            # Convert string of skill names to list and get or create skills
            if isinstance(value, str):
                skill_names = [name.strip() for name in value.split(',') if name.strip()]
                skills = []
                for name in skill_names:
                    skill, created = Skill.objects.get_or_create(
                        name=name,
                        defaults={'slug': slugify(name)}
                    )
                    skills.append(skill)
                return skills
        return super().clean(value)

class FreelancerForm(ModelForm):
    skills_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Python, Django, JavaScript',
            'data-role': 'tagsinput'
        }),
        help_text='Separate skills with commas'
    )
    
    class Meta:
        model = Freelancer
        fields = [
            'title', 'bio', 'hourly_rate', 'experience_years', 
            'education', 'portfolio_website', 'is_available'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'education': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'portfolio_website': forms.URLInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Set initial skills as comma-separated string
            self.fields['skills_input'].initial = ', '.join([skill.name for skill in self.instance.skills.all()])
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_m2m()
            
            # Process skills
            skills_input = self.cleaned_data.get('skills_input', '')
            if skills_input:
                skill_names = [name.strip() for name in skills_input.split(',') if name.strip()]
                skills = []
                for name in skill_names:
                    skill, created = Skill.objects.get_or_create(
                        name=name,
                        defaults={'slug': slugify(name)}
                    )
                    skills.append(skill)
                instance.skills.set(skills)
        return instance

class SkillForm(ModelForm):
    class Meta:
        model = Skill
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }