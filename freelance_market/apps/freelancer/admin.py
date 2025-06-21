from django.contrib import admin
from .models import Freelancer, Skill
from django.utils.html import format_html

class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 20
    ordering = ('name',)

class FreelancerAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'is_available', 'hourly_rate_display', 'experience_display', 'created_at')
    list_filter = ('is_available', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'title')
    list_select_related = ('user',)
    filter_horizontal = ('skills',)
    list_per_page = 20
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'bio', 'skills')
        }),
        ('Professional Details', {
            'fields': ('hourly_rate', 'experience_years', 'portfolio_website')
        }),
        ('Status', {
            'fields': ('is_available',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def hourly_rate_display(self, obj):
        if obj.hourly_rate:
            return f"TZS {obj.hourly_rate}/hr"
        return "-"
    hourly_rate_display.short_description = 'Rate'
    
    def experience_display(self, obj):
        if obj.experience_years:
            return f"{obj.experience_years} year{'s' if obj.experience_years != 1 else ''}"
        return "-"
    experience_display.short_description = 'Experience'

admin.site.register(Skill, SkillAdmin)
admin.site.register(Freelancer, FreelancerAdmin)
