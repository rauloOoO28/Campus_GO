// shared.js - Lógica compartida entre las pantallas del prototipo

// Toggle del sidebar en mobile
document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.querySelector('.mobile-menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');

    if (toggle && sidebar) {
        toggle.addEventListener('click', () => {
            sidebar.classList.add('open');
            if (overlay) overlay.classList.add('show');
        });
    }

    if (overlay) {
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('open');
            overlay.classList.remove('show');
        });
    }

    // Marcar pestaña activa en proto-nav
    const currentPage = window.location.pathname.split('/').pop().replace('.html', '');
    document.querySelectorAll('.proto-nav-link').forEach(link => {
        const href = link.getAttribute('href') || '';
        if (href.includes(currentPage) && currentPage !== '') {
            link.classList.add('active');
        }
    });
});
