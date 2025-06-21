import os
import mimetypes
from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from django.utils.text import slugify
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from .models import Job, JobCategory, JobProposal, ProposalAttachment

class JobForm(forms.ModelForm):
    """Form for creating and updating job postings"""
    
    class Meta:
        model = Job
        fields = [
            'title', 'category', 'description', 'requirements',
            'job_type', 'experience_level', 'budget', 'min_hourly_rate',
            'max_hourly_rate', 'duration', 'deadline', 'status'
        ]
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Describe the job in detail. What needs to be done?'
            }),
            'requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'What skills and experience are required?'
            }),
            'deadline': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': timezone.now().date().isoformat()
            }),
            'status': forms.HiddenInput()
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Apply Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if field_name != 'status':  # Skip status as it's hidden
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control'
        
        # Set required status
        self.fields['budget'].required = False
        self.fields['min_hourly_rate'].required = False
        self.fields['max_hourly_rate'].required = False
        
        # Set category queryset
        self.fields['category'].queryset = JobCategory.objects.all()
        
        # Add placeholders and help text
        self.fields['title'].widget.attrs['placeholder'] = 'e.g., Need a Django developer for a web app'
        self.fields['budget'].widget.attrs['placeholder'] = 'e.g., 500'
        self.fields['min_hourly_rate'].widget.attrs['placeholder'] = 'e.g., 20'
        self.fields['max_hourly_rate'].widget.attrs['placeholder'] = 'e.g., 50'
        self.fields['duration'].widget.attrs['placeholder'] = 'e.g., 1-3 months'
    
    def clean(self):
        cleaned_data = super().clean()
        job_type = cleaned_data.get('job_type')
        budget = cleaned_data.get('budget')
        min_rate = cleaned_data.get('min_hourly_rate')
        max_rate = cleaned_data.get('max_hourly_rate')
        
        # Validate budget based on job type
        if job_type == 'fixed' and not budget:
            self.add_error('budget', 'Budget is required for fixed price jobs')
        
        # Validate hourly rates for hourly jobs
        if job_type == 'hourly':
            if not min_rate or not max_rate:
                if not min_rate:
                    self.add_error('min_hourly_rate', 'Required for hourly jobs')
                if not max_rate:
                    self.add_error('max_hourly_rate', 'Required for hourly jobs')
            elif min_rate and max_rate and min_rate > max_rate:
                self.add_error('max_hourly_rate', 'Maximum rate must be greater than minimum rate')
        
        # Clean HTML from text fields
        text_fields = ['description', 'requirements']
        for field in text_fields:
            if field in cleaned_data:
                cleaned_data[field] = strip_tags(cleaned_data[field])
        
        return cleaned_data
    
    def save(self, commit=True):
        job = super().save(commit=False)
        if not job.pk:  # New job
            job.client = self.user
        
        if commit:
            job.save()
        return job


class MultipleFileInput(forms.ClearableFileInput):
    """Widget for multiple file uploads"""
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        attrs = attrs or {}
        attrs['multiple'] = 'multiple'
        super().__init__(attrs)

    def value_omitted_from_data(self, data, files, name):
        return False

    def value_from_datadict(self, data, files, name):
        if hasattr(files, 'getlist'):
            return files.getlist(name)
        return None


class MultipleFileField(forms.FileField):
    """Field for multiple file uploads"""
    widget = MultipleFileInput
    default_error_messages = {
        'required': 'Please upload at least one file.',
    }

    def clean(self, data, initial=None):
        if self.required and not data:
            raise forms.ValidationError(self.error_messages['required'], code='required')
        return data


class ProposalForm(forms.ModelForm):
    """Form for submitting job proposals with file attachments"""
    attachments = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.txt,.xls,.xlsx,.jpg,.jpeg,.png',
        }),
        help_text='You can upload multiple files (PDF, Word, Excel, Images). Max 10MB per file.'
    )
    
    class Meta:
        model = JobProposal
        fields = ['cover_letter', 'bid_amount', 'estimated_days']
        widgets = {
            'cover_letter': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Write a detailed proposal explaining why you are the best fit for this job...',
                'data-max-words': '1000',
                'oninput': 'countWords(this)'
            }),
            'bid_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'step': '0.01',
                'placeholder': 'e.g., 500.00'
            }),
            'estimated_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'e.g., 14',
                'oninput': 'validateDays(this)'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.job = kwargs.pop('job', None)
        self.freelancer = kwargs.pop('freelancer', None)
        super().__init__(*args, **kwargs)
    
    def clean_bid_amount(self):
        bid_amount = self.cleaned_data.get('bid_amount')
        if bid_amount <= 0:
            raise forms.ValidationError('Bid amount must be greater than 0')
        return bid_amount
    
    def clean_estimated_days(self):
        estimated_days = self.cleaned_data.get('estimated_days')
        if estimated_days <= 0:
            raise forms.ValidationError('Estimated days must be greater than 0')
        return estimated_days
    
    def clean_attachments(self):
        """Validate uploaded files"""
        attachments = self.files.getlist('attachments')
        if not attachments:
            return None
            
        MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
        ALLOWED_TYPES = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'image/jpeg',
            'image/png'
        ]
        
        for attachment in attachments:
            if attachment.size > MAX_UPLOAD_SIZE:
                raise forms.ValidationError(f'File {attachment.name} is too large. Max size is 10MB.')
            if attachment.content_type not in ALLOWED_TYPES:
                raise forms.ValidationError(f'File type {attachment.content_type} is not allowed.')
        
        return attachments
    
    def clean_cover_letter(self):
        """Validate cover letter word count"""
        cover_letter = self.cleaned_data.get('cover_letter')
        words = cover_letter.split()
        if len(words) < 50:
            raise forms.ValidationError('Cover letter should be at least 50 words.')
        if len(words) > 1000:
            raise forms.ValidationError('Cover letter should not exceed 1000 words.')
        return cover_letter
    
    def save(self, commit=True):
        """Save the proposal and handle file uploads"""
        proposal = super().save(commit=False)
        if not proposal.pk:  # New proposal
            proposal.job = self.job
            proposal.freelancer = self.freelancer
        
        if commit:
            proposal.save()
            
            # Save attachments if any
            attachments = self.cleaned_data.get('attachments')
            if attachments:
                for attachment in attachments:
                    proposal_attachment = ProposalAttachment(
                        proposal=proposal,
                        file=attachment,
                        original_filename=attachment.name,
                        file_size=attachment.size,
                        file_type=attachment.content_type
                    )
                    proposal_attachment.save()
        
        return proposal


class JobFilterForm(forms.Form):
    """Form for filtering job listings"""
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    JOB_TYPE_CHOICES = [
        ('', 'All Types'),
        ('fixed', 'Fixed Price'),
        ('hourly', 'Hourly'),
    ]
    
    EXPERIENCE_LEVELS = [
        ('', 'All Levels'),
        ('entry', 'Entry Level'),
        ('intermediate', 'Intermediate'),
        ('expert', 'Expert'),
    ]
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search jobs...',
        })
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    job_type = forms.ChoiceField(
        choices=JOB_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    experience_level = forms.ChoiceField(
        choices=EXPERIENCE_LEVELS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ModelChoiceField(
        queryset=JobCategory.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = JobCategory.objects.all()


class JobCategoryForm(forms.ModelForm):
    """Form for creating and updating job categories"""
    
    class Meta:
        model = JobCategory
        fields = ['name', 'description', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., fas fa-code'}),
        }


class ProposalAttachmentForm(forms.ModelForm):
    """
    Form for uploading attachments to a proposal.
    """
    file = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.txt,.xls,.xlsx,.jpg,.jpeg,.png,.zip,.rar,.7z',
        }),
        help_text='Max file size: 20MB. Allowed file types: PDF, Word, Excel, Images, Archives.'
    )

    class Meta:
        model = ProposalAttachment
        fields = ['file']

    def __init__(self, *args, **kwargs):
        self.proposal = kwargs.pop('proposal', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_file(self):
        """
        Validate the uploaded file.
        """
        file = self.cleaned_data.get('file')
        if not file:
            raise forms.ValidationError('No file was uploaded.')

        # Validate file size (20MB limit)
        max_size = 20 * 1024 * 1024  # 20MB
        if file.size > max_size:
            raise forms.ValidationError(f'File size exceeds the maximum limit of 20MB. Current size: {file.size / (1024 * 1024):.2f}MB')

        # Validate file type
        allowed_types = [
            'image/jpeg', 'image/png', 'image/gif', 'application/pdf',
            'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'text/plain', 'application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed'
        ]

        # Get content type from the file itself or guess from extension
        content_type = None
        if hasattr(file, 'content_type') and file.content_type:
            content_type = file.content_type
        else:
            content_type = mimetypes.guess_type(file.name)[0]

        if content_type not in allowed_types:
            raise forms.ValidationError('File type not allowed. Please upload a valid document, image, or archive.')

        # Additional validation for specific file types
        if content_type == 'application/zip' and not file.name.lower().endswith('.zip'):
            raise forms.ValidationError('Invalid ZIP file. Please upload a valid ZIP archive.')
        elif content_type == 'application/x-rar-compressed' and not file.name.lower().endswith(('.rar', '.cbr')):
            raise forms.ValidationError('Invalid RAR file. Please upload a valid RAR archive.')
        elif content_type == 'application/x-7z-compressed' and not file.name.lower().endswith('.7z'):
            raise forms.ValidationError('Invalid 7z file. Please upload a valid 7z archive.')

        # Set a maximum filename length
        max_filename_length = 100
        if len(file.name) > max_filename_length:
            raise forms.ValidationError(f'Filename is too long. Maximum {max_filename_length} characters allowed.')

        return file

    def save(self, commit=True):
        """
        Save the attachment and associate it with the proposal.
        """
        attachment = super().save(commit=False)
        
        if self.proposal:
            attachment.proposal = self.proposal
        
        if self.user:
            attachment.uploaded_by = self.user
        
        # Set the original filename
        if isinstance(self.cleaned_data['file'], UploadedFile):
            attachment.original_filename = self.cleaned_data['file'].name
        
        # Set file size
        attachment.file_size = self.cleaned_data['file'].size
        
        # Set content type
        if hasattr(self.cleaned_data['file'], 'content_type') and self.cleaned_data['file'].content_type:
            attachment.content_type = self.cleaned_data['file'].content_type
        else:
            attachment.content_type = mimetypes.guess_type(self.cleaned_data['file'].name)[0] or 'application/octet-stream'
        
        if commit:
            attachment.save()
        
        return attachment
