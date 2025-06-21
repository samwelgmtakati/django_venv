from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


register = template.Library()

@register.simple_tag
def star_rating(rating, max_rating=5, show_empty=False):
    """
    Display a star rating.
    
    Args:
        rating: The rating value (0 to max_rating)
        max_rating: Maximum possible rating (default: 5)
        show_empty: If True, shows empty stars up to max_rating
    """
    try:
        rating = float(rating)
        full_stars = int(rating)
        has_half_star = (rating - full_stars) >= 0.5
        
        stars = []
        
        # Add full stars
        for i in range(full_stars):
            stars.append('<i class="bi bi-star-fill text-warning"></i>')
            
        # Add half star if needed
        if has_half_star and full_stars < max_rating:
            stars.append('<i class="bi bi-star-half text-warning"></i>')
            full_stars += 1  # Count the half star as a full one for empty stars
            
        # Add empty stars if needed
        if show_empty:
            empty_stars = max_rating - full_stars
            for i in range(empty_stars):
                stars.append('<i class="bi bi-star text-warning"></i>')
        
        return mark_safe(' '.join(stars))
    except (ValueError, TypeError):
        return ''

@register.simple_tag
def average_rating(reviews, show_empty=False):
    """
    Calculate and display the average rating from a list of reviews.
    
    Args:
        reviews: A queryset or list of review objects with a 'rating' attribute
        show_empty: If True, shows empty stars up to max_rating
    """
    if not reviews or not hasattr(reviews, 'count') or reviews.count() == 0:
        return star_rating(0, show_empty=show_empty)
    
    total = sum(review.rating for review in reviews if hasattr(review, 'rating'))
    avg = total / reviews.count()
    
    return star_rating(avg, show_empty=show_empty)

@register.inclusion_tag('reviews/rating_badge.html')
def rating_badge(rating, size='sm'):
    """
    Display a badge with the rating and stars.
    
    Args:
        rating: The rating value (0 to 5)
        size: Size of the badge (sm, md, lg)
    """
    size_classes = {
        'sm': 'badge-sm',
        'md': '',
        'lg': 'badge-lg',
    }
    
    return {
        'rating': rating,
        'size_class': size_classes.get(size, ''),
    }
