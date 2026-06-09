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

const PROTO_NAV_HTML = `
    <header class="app-header">
        <button class="mobile-menu-toggle" type="button">☰</button>
        <div class="header-logo">CampusGo</div>
        <div class="header-right-spacer"></div>
    </header>
`;

const USER_DATA = window.USER_DATA || {
    is_authenticated: false,
    nombre_completo: 'Invitado',
    rol: 'Invitado',
    email: '',
    initials: 'IV',
    is_admin: false,
};

const API_ENDPOINTS = {
    favoritos: '/api/favoritos/',
    favoritos_guardar: '/api/favoritos/guardar/',
    historial: '/api/historial/',
    historial_registrar: '/api/historial/registrar/',
};

function getCookie(name) {
    const cookieString = document.cookie || '';
    const cookies = cookieString.split(';').map(cookie => cookie.trim());
    const found = cookies.find(cookie => cookie.startsWith(`${name}=`));
    if (!found) return null;
    return decodeURIComponent(found.split('=')[1]);
}

function requestJSON(url, options = {}) {
    const headers = options.headers || {};
    if (!headers['Content-Type'] && !(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }
    if (USER_DATA.is_authenticated) {
        headers['X-CSRFToken'] = getCookie('csrftoken');
    }

    return fetch(url, {
        credentials: 'same-origin',
        ...options,
        headers,
    }).then(async response => {
        const contentType = response.headers.get('content-type') || '';
        const data = contentType.includes('application/json') ? await response.json().catch(() => null) : null;
        if (!response.ok) {
            return Promise.reject({ status: response.status, data });
        }
        return data;
    });
}

function showGuestNotification(message) {
    alert(message || 'Estás en sesión de invitado. Debes iniciar o crear una cuenta para usar esta función.');
}

function renderPanelContent(type, items) {
    if (!USER_DATA.is_authenticated) {
        return `
            <div class="sidebar-panel-empty">
                <div class="sidebar-panel-empty-title">Sesión de invitado</div>
                <p>Para guardar favoritos o ver historial necesitas iniciar sesión o crear una cuenta.</p>
                <div class="sidebar-panel-actions">
                    <a href="${URLS.login}" class="btn btn-secondary">Iniciar sesión</a>
                    <a href="/registro/" class="btn btn-primary">Crear cuenta</a>
                </div>
            </div>
        `;
    }

    if (type === 'favoritos') {
        if (!items.length) {
            return `
                <div class="sidebar-panel-empty">
                    <div class="sidebar-panel-empty-title">No tienes favoritos aún</div>
                    <p>Guarda una escuela desde la página de campus y aparecerá aquí.</p>
                </div>
            `;
        }

        return items.map(item => `
            <div class="sidebar-panel-item">
                <div>
                    <div class="sidebar-panel-item-title">${item.nombre}</div>
                    <div class="sidebar-panel-item-subtitle">${item.direccion || 'Dirección no disponible'}</div>
                </div>
            </div>
        `).join('');
    }

    if (type === 'historial') {
        if (!items.length) {
            return `
                <div class="sidebar-panel-empty">
                    <div class="sidebar-panel-empty-title">Tu historial está vacío</div>
                    <p>Visita una escuela y podrás ver tus últimos lugares consultados aquí.</p>
                </div>
            `;
        }

        return items.map(item => `
            <div class="sidebar-panel-item">
                <div>
                    <div class="sidebar-panel-item-title">${item.nombre}</div>
                    <div class="sidebar-panel-item-subtitle">${item.direccion || 'Dirección no disponible'}</div>
                </div>
            </div>
        `).join('');
    }

    return `<div class="sidebar-panel-empty"><p>Selecciona una sección válida.</p></div>`;
}

function openSidebarPanel(type) {
    const overlay = document.querySelector('.sidebar-overlay');
    const panel = document.querySelector('.sidebar-panel');
    const title = panel.querySelector('.sidebar-panel-title');
    const body = panel.querySelector('.sidebar-panel-body');
    const countLabel = panel.querySelector('.sidebar-panel-title-count');

    panel.classList.add('open');
    if (overlay) overlay.classList.add('show');

    title.textContent = type === 'historial' ? 'Historial' : 'Favoritos';
    countLabel.textContent = type === 'historial' ? '' : '';
    body.innerHTML = '<div class="sidebar-panel-loading">Cargando...</div>';

    if (!USER_DATA.is_authenticated) {
        body.innerHTML = renderPanelContent(type, []);
        return;
    }

    const endpoint = type === 'historial' ? API_ENDPOINTS.historial : API_ENDPOINTS.favoritos;
    requestJSON(endpoint, { method: 'GET' })
        .then(response => {
            body.innerHTML = renderPanelContent(type, response.data || []);
            if (type === 'favoritos') {
                updateFavoritesBadge((response.data || []).length);
            }
        })
        .catch(() => {
            body.innerHTML = '<div class="sidebar-panel-empty"><p>No se pudo cargar la información, intenta de nuevo.</p></div>';
        });
}

function closeSidebarPanel() {
    const overlay = document.querySelector('.sidebar-overlay');
    const panel = document.querySelector('.sidebar-panel');
    if (panel) panel.classList.remove('open');
    if (overlay) overlay.classList.remove('show');
}

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

    const overlay = document.querySelector('.sidebar-overlay');
    const sidebar = document.querySelector('.sidebar');
    const toggle = document.querySelector('.mobile-menu-toggle');

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

function updateFavoritesBadge(count) {
    const badge = document.getElementById('sidebar-favorites-count');
    if (!badge) return;
    badge.textContent = count;
    badge.style.display = count > 0 ? 'inline-flex' : 'none';
}

function saveFavorite(codigo, label) {
    if (!USER_DATA.is_authenticated) {
        showGuestNotification();
        return;
    }

    requestJSON(API_ENDPOINTS.favoritos_guardar, {
        method: 'POST',
        body: JSON.stringify({ codigo }),
    })
        .then(response => {
            alert(`"${label}" se ha guardado en tus favoritos.`);
            loadFavoritesCount();
        })
        .catch(error => {
            alert(error?.data?.message || 'No se pudo guardar tu favorito.');
        });
}

function loadFavoritesCount() {
    if (!USER_DATA.is_authenticated) {
        updateFavoritesBadge(0);
        return;
    }

    requestJSON(API_ENDPOINTS.favoritos, { method: 'GET' })
        .then(response => {
            updateFavoritesBadge((response.data || []).length);
        })
        .catch(() => {
            updateFavoritesBadge(0);
        });
}

function maybeRegisterHistory(codigo) {
    if (!USER_DATA.is_authenticated) {
        return;
    }

    requestJSON(API_ENDPOINTS.historial_registrar, {
        method: 'POST',
        body: JSON.stringify({ codigo }),
    }).catch(() => {
        // No hay problema si no se guarda historial
    });
}

function attachShellHandlers() {
    const favoritesLink = Array.from(document.querySelectorAll('.sidebar-link')).find(link => link.textContent.includes('Favoritos'));
    const historyLink = Array.from(document.querySelectorAll('.sidebar-link')).find(link => link.textContent.includes('Historial'));
    const overlay = document.querySelector('.sidebar-overlay');
    const panelClose = document.querySelector('.sidebar-panel-close');

    if (favoritesLink) {
        favoritesLink.addEventListener('click', event => {
            event.preventDefault();
            openSidebarPanel('favoritos');
        });
    }
    if (historyLink) {
        historyLink.addEventListener('click', event => {
            event.preventDefault();
            openSidebarPanel('historial');
        });
    }

    if (overlay) {
        overlay.addEventListener('click', () => {
            closeSidebarPanel();
        });
    }
    if (panelClose) {
        panelClose.addEventListener('click', closeSidebarPanel);
    }

    document.querySelectorAll('[data-action="guardar-favorito"]').forEach(button => {
        button.addEventListener('click', event => {
            event.preventDefault();
            event.stopPropagation();
            const codigo = button.dataset.campusCodigo;
            const label = button.dataset.campusNombre || 'Campus';
            saveFavorite(codigo, label);
        });
    });

    document.querySelectorAll('.campus-card-link').forEach(link => {
        link.addEventListener('click', event => {
            const card = link.closest('.campus-card');
            const codigo = card?.dataset.campusCodigo;
            if (codigo && USER_DATA.is_authenticated) {
                event.preventDefault();
                maybeRegisterHistory(codigo);
                window.location.href = link.href;
            }
        });
    });
}

function generateSidebarHTML() {
    const initials = USER_DATA.initials || 'IV';
    const nombre = USER_DATA.nombre_completo || 'Invitado';
    const rol = USER_DATA.rol || 'Invitado';
    const isAdmin = USER_DATA.is_admin === true;

    let adminMenuHTML = '';
    if (isAdmin) {
        adminMenuHTML = `
            <a href="${URLS.admin}" data-key="admin" class="sidebar-link">
                <i class="bi bi-shield-lock-fill"></i> Administración
            </a>
        `;
    }

    const logoutMenuHTML = USER_DATA.is_authenticated ? `
        <a href="/logout/" class="sidebar-link">
            <i class="bi bi-box-arrow-right"></i> Cerrar sesión
        </a>
    ` : '';

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
                <span class="badge-count" id="sidebar-favorites-count" style="display: none;">0</span>
            </a>
            <a href="#" class="sidebar-link">
                <i class="bi bi-clock-history"></i> Historial
            </a>
        </nav>

        <div class="sidebar-section-label">Sistema</div>
        <nav class="sidebar-nav">
            ${adminMenuHTML}
            <a href="#" class="sidebar-link">
                <i class="bi bi-gear-fill"></i> Configuración
            </a>
            ${logoutMenuHTML}
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
    <div class="sidebar-panel" aria-hidden="true">
        <div class="sidebar-panel-header">
            <div>
                <div class="sidebar-panel-title">Favoritos</div>
                <div class="sidebar-panel-title-count"></div>
            </div>
            <button type="button" class="sidebar-panel-close" aria-label="Cerrar panel">×</button>
        </div>
        <div class="sidebar-panel-body"></div>
    </div>
    <div class="sidebar-overlay"></div>
`;
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
    attachShellHandlers();
    loadFavoritesCount();
    setupPasswordToggles();
});