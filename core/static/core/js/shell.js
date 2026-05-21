// shell.js - Inyecta el sidebar y barra de navegación del prototipo
// ============================================================
// IMPORTANTE: Las rutas aquí deben coincidir con tu urls.py
// ============================================================
// Tu urls.py de Django tiene estas rutas:
//   ''             → name='home'
//   'login/'       → name='login'
//   'campus/'      → name='campus'
//   'mapa/'        → name='map'
//   'detalle/'     → name='detail'
//   'ruta/'        → name='route'
//   'qr/'          → name='qr'
//   'admin-panel/' → name='admin_panel'
// ============================================================

const URLS = {
    login:  '/login/',
    campus: '/campus/',
    map:    '/mapa/',
    detail: '/detalle/',
    route:  '/ruta/',
    qr:     '/qr/',
    admin:  '/admin-panel/'
};

// Datos globales del usuario (se pasan desde las plantillas)
const USER_DATA = window.USER_DATA || {
    is_authenticated: false,
    nombre_completo: 'Invitado',
    rol: 'Invitado',
    email: '',
    initials: 'IV'
};

function generateSidebarHTML() {
    const initials = USER_DATA.initials || 'IV';
    const nombre = USER_DATA.nombre_completo || 'Invitado';
    const rol = USER_DATA.rol || 'Invitado';
    
    return `
    <aside class="sidebar">
        <div class="sidebar-brand">
            <div class="sidebar-brand-icon"><i class="bi bi-geo-alt-fill"></i></div>
            <div class="sidebar-brand-text">Campus<span>Go</span></div>
        </div>

        <div class="sidebar-section-label">Navegación</div>
        <nav class="sidebar-nav">
            <a href="${URLS.campus}" data-key="campus" class="sidebar-link">
                <i class="bi bi-buildings"></i> Campus
            </a>
            <a href="${URLS.map}" data-key="map" class="sidebar-link">
                <i class="bi bi-map-fill"></i> Mapa
            </a>
            <a href="${URLS.route}" data-key="route" class="sidebar-link">
                <i class="bi bi-signpost-split-fill"></i> Rutas
            </a>
            <a href="${URLS.qr}" data-key="qr" class="sidebar-link">
                <i class="bi bi-qr-code-scan"></i> Escáner QR
            </a>
        </nav>

        <div class="sidebar-section-label">Personal</div>
        <nav class="sidebar-nav">
            <a href="#" class="sidebar-link">
                <i class="bi bi-bookmark-fill"></i> Favoritos
                <span class="badge-count">5</span>
            </a>
            <a href="#" class="sidebar-link">
                <i class="bi bi-clock-history"></i> Historial
            </a>
        </nav>

        <div class="sidebar-section-label">Sistema</div>
        <nav class="sidebar-nav">
            <a href="${URLS.admin}" data-key="admin" class="sidebar-link">
                <i class="bi bi-shield-lock-fill"></i> Administración
            </a>
            <a href="#" class="sidebar-link">
                <i class="bi bi-gear-fill"></i> Configuración
            </a>
        </nav>

        <div class="sidebar-footer">
            <div class="sidebar-user">
                <div class="user-avatar">${initials}</div>
                <div class="sidebar-user-info">
                    <div class="sidebar-user-name">${nombre}</div>
                    <div class="sidebar-user-role">${rol}</div>
                </div>
                <i class="bi bi-chevron-right" style="color: var(--color-text-muted); font-size: 14px;"></i>
            </div>
        </div>
    </aside>
    <div class="sidebar-overlay"></div>
`;
}

const PROTO_NAV_HTML = `
    <header class="app-header">
        <button class="mobile-menu-toggle" type="button">☰</button>
        <div class="header-logo">CampusGo</div>
        <div class="header-right-spacer"></div>
    </header>
`;

function injectShell() {
    const activeKey = document.body.dataset.active;

    // Inyectar header principal en lugar de la barra antigua
    const navMount = document.querySelector('[data-mount="proto-nav"]');
    if (navMount) navMount.outerHTML = PROTO_NAV_HTML;

    // Inyectar sidebar (generarla aquí para que tenga acceso a USER_DATA)
    const sidebarMount = document.querySelector('[data-mount="sidebar"]');
    if (sidebarMount) sidebarMount.outerHTML = generateSidebarHTML();

    // Marcar la pantalla activa
    if (activeKey) {
        document.querySelectorAll(`[data-key="${activeKey}"]`).forEach(el => {
            el.classList.add('active');
        });
    }

    // Toggle del sidebar
    const toggle = document.querySelector('.mobile-menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');

    if (toggle && sidebar) {
        toggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
            if (overlay) overlay.classList.toggle('show');
        });
    }

    if (overlay && sidebar) {
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('open');
            overlay.classList.remove('show');
        });
    }
}

function setupPasswordToggles() {
    const toggles = document.querySelectorAll('.password-toggle');
    toggles.forEach(button => {
        button.addEventListener('click', () => {
            const group = button.closest('.login-form-group');
            if (!group) return;
            const input = group.querySelector('input[type="password"], input[type="text"]');
            if (!input) return;

            const isPassword = input.type === 'password';
            input.type = isPassword ? 'text' : 'password';
            const icon = button.querySelector('i');
            if (icon) {
                icon.classList.toggle('bi-eye-fill', !isPassword);
                icon.classList.toggle('bi-eye-slash-fill', isPassword);
            }
            button.setAttribute('aria-label', isPassword ? 'Ocultar contraseña' : 'Mostrar contraseña');
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    injectShell();
    setupPasswordToggles();
});