from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Review

class ReviewForm(forms.ModelForm):
    """Form for submitting reviews with star ratings."""
    RATING_CHOICES = [
        (5, '5 - Excellent'),
        (4, '4 - Very Good'),
        (3, '3 - Average'),
        (2, '2 - Below Average'),
        (1, '1 - Poor'),
    ]
    
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'd-none',  # Hide the default radio inputs
        }),
        required=True,
        label=_('Rating'),
        help_text=_('Click on the stars to rate')
    )
    
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': _('Share your experience (optional)')
            }),
        }
        labels = {
            'comment': _('Your Review'),
        }
        help_texts = {
            'comment': _('Your feedback helps improve our service.'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial rating to 5 (default)
        if not self.initial.get('rating'):
            self.initial['rating'] = '5'

    def clean_rating(self):
        """Validate that a rating was selected."""
        rating = self.cleaned_data.get('rating')
        if not rating:
            raise ValidationError(_('Please select a rating'))
        try:
            return int(rating)
        except (TypeError, ValueError):
            raise ValidationError(_('Invalid rating value'))
