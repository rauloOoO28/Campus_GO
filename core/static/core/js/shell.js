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

const SIDEBAR_HTML = `
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
                <div class="user-avatar">OS</div>
                <div class="sidebar-user-info">
                    <div class="sidebar-user-name">Oscar Sánchez</div>
                    <div class="sidebar-user-role">Estudiante</div>
                </div>
                <i class="bi bi-chevron-right" style="color: var(--color-text-muted); font-size: 14px;"></i>
            </div>
        </div>
    </aside>
    <div class="sidebar-overlay"></div>
`;

const PROTO_NAV_HTML = `
    <nav class="proto-nav">
        <div class="proto-nav-brand">
            <span class="dot"></span>
            CampusGo · Prototipo
        </div>
        <div class="proto-nav-links">
            <a href="${URLS.login}"  data-key="login"  class="proto-nav-link"><span class="num">0</span> Login</a>
            <a href="${URLS.campus}" data-key="campus" class="proto-nav-link"><span class="num">CU-01</span> Campus</a>
            <a href="${URLS.map}"    data-key="map"    class="proto-nav-link"><span class="num">CU-02</span> Mapa</a>
            <a href="${URLS.detail}" data-key="detail" class="proto-nav-link"><span class="num">CU-05</span> Ubicación</a>
            <a href="${URLS.route}"  data-key="route"  class="proto-nav-link"><span class="num">CU-03</span> Ruta</a>
            <a href="${URLS.qr}"     data-key="qr"     class="proto-nav-link"><span class="num">CU-04</span> QR</a>
            <a href="${URLS.admin}"  data-key="admin"  class="proto-nav-link"><span class="num">CU-06</span> Admin</a>
        </div>
        <div class="proto-nav-info">v1.0 · Mockup</div>
    </nav>
`;

function injectShell() {
    const activeKey = document.body.dataset.active;

    // Inyectar proto-nav
    const navMount = document.querySelector('[data-mount="proto-nav"]');
    if (navMount) navMount.outerHTML = PROTO_NAV_HTML;

    // Inyectar sidebar
    const sidebarMount = document.querySelector('[data-mount="sidebar"]');
    if (sidebarMount) sidebarMount.outerHTML = SIDEBAR_HTML;

    // Marcar la pantalla activa
    if (activeKey) {
        document.querySelectorAll(`[data-key="${activeKey}"]`).forEach(el => {
            el.classList.add('active');
        });
    }

    // Toggle del sidebar en mobile
    const toggle = document.querySelector('.mobile-menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');

    if (toggle && sidebar) {
        toggle.addEventListener('click', () => {
            sidebar.classList.add('open');
            if (overlay) overlay.classList.add('show');
        });
    }

    if (overlay && sidebar) {
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('open');
            overlay.classList.remove('show');
        });
    }
}

document.addEventListener('DOMContentLoaded', injectShell);