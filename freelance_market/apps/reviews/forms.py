from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Review, ReviewHelpfulVote
from django.utils import timezone

class ReviewForm(forms.ModelForm):
    """Form for submitting detailed reviews with multiple rating criteria."""
    RATING_CHOICES = [
        (5, '5 - Excellent'),
        (4, '4 - Very Good'),
        (3, '3 - Average'),
        (2, '2 - Below Average'),
        (1, '1 - Poor'),
    ]
    
    # Main rating
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'd-none'}),
        required=True,
        label=_('Overall Rating'),
        help_text=_('Your overall satisfaction with this user')
    )
    
    # Detailed ratings
    communication_rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'd-none'}),
        required=True,
        label=_('Communication'),
        help_text=_('How clearly and effectively they communicated')
    )
    
    quality_rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'd-none'}),
        required=True,
        label=_('Quality of Work'),
        help_text=_('The quality of work delivered')
    )
    
    deadline_rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'd-none'}),
        required=True,
        label=_('Meeting Deadlines'),
        help_text=_('How well they met agreed-upon deadlines')
    )
    
    professionalism_rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'd-none'}),
        required=True,
        label=_('Professionalism'),
        help_text=_('Their level of professionalism')
    )
    
    class Meta:
        model = Review
        fields = [
            'rating',
            'communication_rating',
            'quality_rating',
            'deadline_rating',
            'professionalism_rating',
            'comment'
        ]
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': _('Share your detailed experience (optional)')
            }),
        }
        labels = {
            'comment': _('Your Detailed Review'),
        }
        help_texts = {
            'comment': _('Your detailed feedback helps others make better decisions.'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default ratings
        default_rating = '5'
        for field in self.fields:
            if field.endswith('_rating') and not self.initial.get(field):
                self.initial[field] = default_rating
        
        # Add CSS classes to all rating fields
        for field_name, field in self.fields.items():
            if field_name.endswith('_rating'):
                field.widget.attrs.update({
                    'class': 'rating-input',
                    'data-stars': '5'
                })

    def clean(self):
        cleaned_data = super().clean()
        
        # Convert all rating fields to integers
        for field in self.fields:
            if field.endswith('_rating') and field in cleaned_data:
                try:
                    cleaned_data[field] = int(cleaned_data[field])
                except (ValueError, TypeError):
                    self.add_error(field, _('Please select a valid rating'))
        
        return cleaned_data


class ReviewResponseForm(forms.ModelForm):
    """Form for responding to a review."""
    class Meta:
        model = Review
        fields = ['response']
        widgets = {
            'response': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Write your response here...')
            }),
        }
        labels = {
            'response': _('Your Response'),
        }
    
    def save(self, commit=True):
        review = super().save(commit=False)
        review.response_date = timezone.now()
        if commit:
            review.save(update_fields=['response', 'response_date'])
        return review


class ReviewHelpfulVoteForm(forms.ModelForm):
    """Form for marking a review as helpful."""
    class Meta:
        model = ReviewHelpfulVote
        fields = ['is_helpful']
        widgets = {
            'is_helpful': forms.HiddenInput()
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.review = kwargs.pop('review', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        if not self.user or not self.review:
            raise ValidationError(_('User and review are required'))
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = self.user
        instance.review = self.review
        if commit:
            instance.save()
        return instance
