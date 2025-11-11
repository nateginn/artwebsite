document.addEventListener('DOMContentLoaded', function() {
    // Mobile tooltip handler
    if (window.innerWidth < 640) {
        const buttons = document.querySelectorAll('a[data-tooltip-id]');
        buttons.forEach((button) => {
            const tooltipId = button.getAttribute('data-tooltip-id');
            const tooltip = document.getElementById(tooltipId);
            if (!tooltip) return;

            button.addEventListener('touchstart', function() {
                tooltip.style.opacity = '1';
            });
            button.addEventListener('touchend', function() {
                setTimeout(function() {
                    tooltip.style.opacity = '0';
                }, 1500);
            });
        });
    }

    // Set main content padding top to avoid overlap with fixed header
    const header = document.querySelector('header');
    const mainContent = document.getElementById('main-content');
    if (header && mainContent) {
        const headerHeight = header.offsetHeight;
        mainContent.style.paddingTop = headerHeight + 'px';
    }
});
