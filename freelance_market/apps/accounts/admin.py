from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile

class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    
    list_display = ('username', 'email', 'first_name', 'last_name', 
                   'is_admin', 'is_client', 'is_freelancer', 'is_active', 'date_joined')
    list_filter = ('is_admin', 'is_client', 'is_freelancer', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'profile_picture')}),
        (_('Permissions'), {'fields': ('is_active', 'is_admin', 'is_client', 'is_freelancer')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    filter_horizontal = ()

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'website')
    search_fields = ('user__username', 'location')
    list_filter = ('location',)

admin.site.register(User, UserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
