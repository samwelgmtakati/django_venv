from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    ROLE_CHOICES = [
        ('client', 'I want to hire freelancers'),
        ('freelancer', 'I want to offer my services'),
    ]
    
    email = forms.EmailField(required=True, help_text='Required. Enter a valid email address.')
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    user_type = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect,
        required=True,
        label='I am a',
        initial='client'  # Set a default value
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'user_type')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with that email already exists.")
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        # Set the role on the user model directly
        user_type = self.cleaned_data.get('user_type')
        if user_type == 'client':
            user.is_client = True
            user.is_freelancer = False
        elif user_type == 'freelancer':
            user.is_freelancer = True
            user.is_client = False
        
        if commit:
            user.save()
            # Update the user's groups and permissions if needed
            self.save_m2m()
        
        return user
