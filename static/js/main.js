
// NHANES Research Platform - Main JS
document.addEventListener('DOMContentLoaded', function() {
    // Initialize navigation
    const nav = document.querySelector('nav');
    if (nav) {
        window.addEventListener('scroll', function() {
            nav.classList.toggle('scrolled', window.scrollY > 50);
        });
    }
    
    // Initialize smooth scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) target.scrollIntoView({ behavior: 'smooth' });
        });
    });
    
    // Initialize data tables if present
    if (typeof DataTable !== 'undefined') {
        document.querySelectorAll('.data-table').forEach(table => {
            new DataTable(table);
        });
    }
});
