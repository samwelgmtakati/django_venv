document.addEventListener('DOMContentLoaded', function() {
    // Intersection Observer for better performance
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const animateSkill = (entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const progressBar = entry.target.querySelector('.progress-bar');
                if (progressBar && !progressBar.classList.contains('animated')) {
                    const width = progressBar.getAttribute('aria-valuenow') + '%';
                    progressBar.style.width = width;
                    progressBar.classList.add('animated');
                    
                    // Animate the percentage counter
                    const percentageElement = entry.target.querySelector('.skill-percentage');
                    if (percentageElement) {
                        const target = parseInt(progressBar.getAttribute('aria-valuenow'));
                        let current = 0;
                        const duration = 1000; // 1 second animation
                        const startTime = performance.now();
                        
                        const animateCounter = (timestamp) => {
                            const elapsed = timestamp - startTime;
                            const progress = Math.min(elapsed / duration, 1);
                            current = Math.floor(progress * target);
                            
                            percentageElement.textContent = current + '%';
                            
                            if (progress < 1) {
                                requestAnimationFrame(animateCounter);
                            } else {
                                percentageElement.textContent = target + '%';
                            }
                        };
                        
                        requestAnimationFrame(animateCounter);
                    }
                }
            }
        });
    };

    // Initialize observer for each skill item
    const skillItems = document.querySelectorAll('.skill-item');
    const observer = new IntersectionObserver(animateSkill, observerOptions);
    
    // Observe each skill item
    skillItems.forEach(item => {
        // Set initial state
        const progressBar = item.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = '0';
        }
        observer.observe(item);
    });
    
    // Fallback for browsers that don't support IntersectionObserver
    if (!('IntersectionObserver' in window)) {
        const animateOnScroll = () => {
            const progressBars = document.querySelectorAll('.progress-bar:not(.animated)');
            
            progressBars.forEach(bar => {
                const rect = bar.getBoundingClientRect();
                const isVisible = (rect.top >= 0) && 
                               (rect.top <= (window.innerHeight || document.documentElement.clientHeight));
                
                if (isVisible) {
                    const width = bar.getAttribute('aria-valuenow') + '%';
                    bar.style.width = width;
                    bar.classList.add('animated');
                    
                    const percentageElement = bar.closest('.skill-item').querySelector('.skill-percentage');
                    if (percentageElement) {
                        const target = parseInt(bar.getAttribute('aria-valuenow'));
                        let current = 0;
                        const duration = 1000;
                        const startTime = performance.now();
                        
                        const animateCounter = (timestamp) => {
                            const elapsed = timestamp - startTime;
                            const progress = Math.min(elapsed / duration, 1);
                            current = Math.floor(progress * target);
                            
                            percentageElement.textContent = current + '%';
                            
                            if (progress < 1) {
                                requestAnimationFrame(animateCounter);
                            } else {
                                percentageElement.textContent = target + '%';
                            }
                        };
                        
                        requestAnimationFrame(animateCounter);
                    }
                }
            });
        };
        
        // Run on events
        const runAnimations = () => {
            requestAnimationFrame(animateOnScroll);
        };
        
        // Initial check
        runAnimations();
        
        // Add event listeners
        window.addEventListener('scroll', runAnimations, { passive: true });
        window.addEventListener('resize', runAnimations, { passive: true });
    }
});
