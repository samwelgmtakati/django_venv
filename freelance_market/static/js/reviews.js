/**
 * Review form handling and star rating functionality
 */

$(document).ready(function() {
    // Rating descriptions for different rating types
    const RATING_DESCRIPTIONS = {
        'overall': {
            '1': gettext('Poor (1/5)'),
            '2': gettext('Fair (2/5)'),
            '3': gettext('Average (3/5)'),
            '4': gettext('Good (4/5)'),
            '5': gettext('Excellent (5/5)')
        },
        'communication': {
            '1': gettext('Poor communication'),
            '2': gettext('Fair communication'),
            '3': gettext('Average communication'),
            '4': gettext('Good communication'),
            '5': gettext('Excellent communication')
        },
        'quality': {
            '1': gettext('Poor quality of work'),
            '2': gettext('Fair quality of work'),
            '3': gettext('Average quality of work'),
            '4': gettext('Good quality of work'),
            '5': gettext('Excellent quality of work')
        },
        'deadline': {
            '1': gettext('Missed all deadlines'),
            '2': gettext('Missed some deadlines'),
            '3': gettext('Met deadlines'),
            '4': gettext('Delivered on time'),
            '5': gettext('Delivered before deadline')
        },
        'professionalism': {
            '1': gettext('Very unprofessional'),
            '2': gettext('Somewhat unprofessional'),
            '3': gettext('Neutral'),
            '4': gettext('Professional'),
            '5': gettext('Extremely professional')
        }
    };

    // Initialize all star ratings
    $('.star-rating').each(function() {
        const $container = $(this);
        const ratingType = $container.data('rating-type');
        const $inputs = $container.find('input[type="radio"]');
        const $labels = $container.find('label');
        const $ratingText = $(`#${ratingType}-rating-text`);
        
        // Set initial state
        updateStarRating($container, $inputs, $labels, $ratingText, ratingType);
        
        // Handle click on stars
        $labels.on('click', function() {
            const $clickedStar = $(this);
            const $input = $('#' + $clickedStar.attr('for'));
            
            // Update the checked state
            $inputs.prop('checked', false);
            $input.prop('checked', true);
            
            // Update the visual state
            updateStarRating($container, $inputs, $labels, $ratingText, ratingType);
            
            // Update the overall rating if needed
            if (ratingType !== 'overall') {
                updateOverallRating();
            }
        });
        
        // Handle hover effects
        $labels.on('mouseenter', function() {
            const $hoveredStar = $(this);
            const starValue = $('#' + $hoveredStar.attr('for')).val();
            
            // Highlight stars up to the hovered one
            $labels.each(function() {
                const $star = $(this);
                const $starInput = $('#' + $star.attr('for'));
                
                if ($starInput.val() <= starValue) {
                    $star.find('i')
                        .removeClass('bi-star')
                        .addClass('bi-star-fill');
                } else {
                    $star.find('i')
                        .removeClass('bi-star-fill')
                        .addClass('bi-star');
                }
            });
            
            // Update rating text on hover
            if ($ratingText.length) {
                $ratingText.text(RATING_DESCRIPTIONS[ratingType][starValue] || '');
            }
        });
        
        // Reset to actual state on mouse leave
        $container.on('mouseleave', function() {
            updateStarRating($container, $inputs, $labels, $ratingText, ratingType);
        });
    });
    
    // Function to update star rating display
    function updateStarRating($container, $inputs, $labels, $ratingText, ratingType) {
        const $checkedInput = $inputs.filter(':checked');
        const value = $checkedInput.val() || '0';
        
        // Update star icons
        $labels.each(function() {
            const $star = $(this);
            const $starInput = $('#' + $star.attr('for'));
            const $icon = $star.find('i');
            
            if ($starInput.val() <= value) {
                $icon.removeClass('bi-star').addClass('bi-star-fill');
            } else {
                $icon.removeClass('bi-star-fill').addClass('bi-star');
            }
        });
        
        // Update rating text
        if ($ratingText.length) {
            $ratingText.text(RATING_DESCRIPTIONS[ratingType][value] || '');
        }
    }
    
    // Function to calculate and update overall rating
    function updateOverallRating() {
        const ratings = [
            parseInt($('input[name="communication_rating"]:checked').val() || 0),
            parseInt($('input[name="quality_rating"]:checked').val() || 0),
            parseInt($('input[name="deadline_rating"]:checked').val() || 0),
            parseInt($('input[name="professionalism_rating"]:checked').val() || 0)
        ];
        
        // Calculate average (only if all ratings are provided)
        if (ratings.every(r => r > 0)) {
            const avgRating = Math.round((ratings.reduce((a, b) => a + b, 0) / ratings.length) * 2) / 2;
            
            // Update the overall rating input
            $('input[name="rating"]').val(Math.round(avgRating));
            
            // Update the visual display
            const $overallRating = $('.star-rating[data-rating-type="overall"]');
            const $inputs = $overallRating.find('input[type="radio"]');
            const $labels = $overallRating.find('label');
            const $ratingText = $('#overall-rating-text');
            
            // Check the appropriate radio button
            $inputs.prop('checked', false);
            $(`#rating_${Math.round(avgRating)}`).prop('checked', true);
            
            // Update the display
            updateStarRating($overallRating, $inputs, $labels, $ratingText, 'overall');
        }
    }
    
    // Form submission handling
    $('#review-form').on('submit', function(e) {
        e.preventDefault();
        
        const $form = $(this);
        const $submitBtn = $form.find('button[type="submit"]');
        const originalBtnText = $submitBtn.html();
        
        // Disable submit button and show loading state
        $submitBtn.prop('disabled', true).html(
            '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span> ' +
            gettext('Submitting...')
        );
        
        // Clear previous alerts
        $('#review-alerts').empty();
        
        // Submit form via AJAX
        $.ajax({
            type: 'POST',
            url: $form.attr('action'),
            data: $form.serialize(),
            success: function(response) {
                if (response.redirect) {
                    window.location.href = response.redirect;
                } else {
                    // Show success message
                    showAlert('success', gettext('Thank you for your review!'));
                    
                    // Redirect after delay
                    setTimeout(function() {
                        window.location.href = response.redirect || window.location.href;
                    }, 2000);
                }
            },
            error: function(xhr) {
                let errorMessage = gettext('An error occurred while submitting your review. Please try again.');
                
                // Try to get error message from response
                try {
                    const response = xhr.responseJSON || {};
                    if (response.error) {
                        errorMessage = response.error;
                    } else if (response.errors) {
                        // Handle form errors
                        errorMessage = Object.values(response.errors).flat().join(' ');
                    } else if (xhr.responseText) {
                        // Handle HTML response (form errors)
                        const $response = $(xhr.responseText);
                        const formErrors = $response.find('.alert-danger, .invalid-feedback').first();
                        if (formErrors.length) {
                            errorMessage = formErrors.text().trim();
                        }
                    }
                } catch (e) {
                    console.error('Error parsing error response:', e);
                }
                
                // Show error message
                showAlert('danger', errorMessage);
                
                // Re-enable submit button
                $submitBtn.prop('disabled', false).html(originalBtnText);
                
                // Scroll to top to show error
                $('html, body').animate({
                    scrollTop: 0
                }, 500);
            }
        });
    });
    
    // Helper function to show alert messages
    function showAlert(type, message) {
        const $alert = $(
            '<div class="alert alert-' + type + ' alert-dismissible fade show" role="alert">' +
            '   ' + message +
            '   <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="' + gettext('Close') + '"></button>' +
            '</div>'
        );
        
        $('#review-alerts').append($alert);
    }
});
