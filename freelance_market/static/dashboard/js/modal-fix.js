// Handle delete functionality with confirmation
document.addEventListener('DOMContentLoaded', function() {
    // Handle delete button clicks
    document.querySelectorAll('.delete-service').forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const form = this.closest('form');
            
            if (confirm('Are you sure you want to delete this service? This action cannot be undone.')) {
                form.submit();
            }
        });
    });
});
