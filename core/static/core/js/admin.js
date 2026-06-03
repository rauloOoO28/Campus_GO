// admin.js - Funcionalidad dinámica del panel de administración
// ============================================================

const ADMIN_API = {
    stats: '/api/admin/stats/',
    ubicaciones: '/api/admin/ubicaciones/',
    edificios: '/api/admin/edificios/',
    campus: '/api/admin/campus/',
    usuarios_stats: '/api/admin/usuarios/stats/',
    usuarios: '/api/admin/usuarios/',
};

console.log('admin.js loaded');

let currentTab = 'ubicaciones';
let allData = {
    stats: null,
    ubicaciones: [],
    edificios: [],
    campus: [],
    usuarios: [],
};
// Paginación
const PAGE_SIZE = 6;
let currentPage = 1;
let totalUbicaciones = 0;


// ============================================================
// CARGA DE DATOS
// ============================================================

async function cargarStats() {
    try {
        const res = await fetch(ADMIN_API.stats);
        const json = await res.json();
        if (json.status === 'success') {
            allData.stats = json.data;
            actualizarStatsUI();
        }
    } catch (e) {
        console.error('Error cargando stats:', e);
    }
}

async function cargarUbicaciones() {
    try {
        const res = await fetch(ADMIN_API.ubicaciones);
        const json = await res.json();
        if (json.status === 'success') {
            // Soportar respuestas paginadas o listas planas
            allData.ubicaciones = Array.isArray(json.data) ? json.data : (json.results || []);
            totalUbicaciones = json.total || json.count || allData.ubicaciones.length;
            currentPage = 1;
            actualizarPaginacion(totalUbicaciones);
            renderCurrentPage();
        }
    } catch (e) {
        console.error('Error cargando ubicaciones:', e);
    }
}

async function cargarEdificios() {
    try {
        const res = await fetch(ADMIN_API.edificios);
        const json = await res.json();
        if (json.status === 'success') {
            allData.edificios = json.data;
            renderTablaEdificios();
        }
    } catch (e) {
        console.error('Error cargando edificios:', e);
    }
}

async function cargarCampus() {
    try {
        const res = await fetch(ADMIN_API.campus);
        const json = await res.json();
        if (json.status === 'success') {
            allData.campus = json.data;
            renderTablaCampus();
        }
    } catch (e) {
        console.error('Error cargando campus:', e);
    }
}

async function cargarUsuarios() {
    try {
        const res = await fetch(ADMIN_API.usuarios);
        const json = await res.json();
        if (json.status === 'success') {
            allData.usuarios = json.data;
            renderTablaUsuarios();
        }
    } catch (e) {
        console.error('Error cargando usuarios:', e);
    }
}

async function cargarTodosLosStats() {
    try {
        const res = await fetch(ADMIN_API.usuarios_stats);
        const json = await res.json();
        if (json.status === 'success') {
            allData.usuarios_stats = json.data;
            actualizarStatsUI();
        }
    } catch (e) {
        console.error('Error cargando usuarios stats:', e);
    }
}

// ============================================================
// ACTUALIZACIÓN DE UI - STATS
// ============================================================

function actualizarStatsUI() {
    if (!allData.stats) return;
    
    // Actualizar tarjetas de stats
    const stats = allData.stats;
    
    // Campus
    const campusCard = document.querySelector('.admin-stat-card.featured .admin-stat-value');
    if (campusCard) campusCard.textContent = stats.campus_activos || 0;
    
    // Ubicaciones
    const ubicacionesCards = document.querySelectorAll('.admin-stat-card .admin-stat-value');
    if (ubicacionesCards[1]) ubicacionesCards[1].textContent = stats.ubicaciones_registradas || 0;
    
    // QR
    if (ubicacionesCards[2]) ubicacionesCards[2].textContent = stats.qr_generados || 0;
    
    // Usuarios (si existe usuarios_stats)
    if (allData.usuarios_stats && ubicacionesCards[3]) {
        ubicacionesCards[3].textContent = allData.usuarios_stats.usuarios_registrados || 0;
    }
}

// ============================================================
// RENDER TABLAS
// ============================================================

function renderTablaUbicaciones() {
    const tbody = document.querySelector('.admin-table tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    const items = arguments[0] || allData.ubicaciones;
    
    items.forEach(ub => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>
                <div class="table-row-name">
                    <div class="icon-box"><i class="bi bi-geo-alt-fill"></i></div>
                    <div>
                        <div class="table-row-name-text">${ub.nombre}</div>
                        <div class="table-row-name-meta">Piso ${ub.piso} · Capacidad ${ub.capacidad}</div>
                    </div>
                </div>
            </td>
            <td><span class="tag">${ub.tipo}</span></td>
            <td>${ub.edificio}</td>
            <td><span class="qr-code-cell">${ub.tiene_qr ? 'QR-' + ub.id : 'N/A'}</span></td>
            <td><span class="status-chip ${ub.activo ? 'confirmed' : 'inactive'}"><i class="bi ${ub.activo ? 'bi-check-circle-fill' : 'bi-x-circle-fill'}"></i> ${ub.activo ? 'Activo' : 'Inactivo'}</span></td>
            <td>
                <div class="table-actions">
                    <button class="admin-action-btn" title="Ver" onclick="verUbicacion(${ub.id})"><i class="bi bi-eye-fill"></i></button>
                    <button class="admin-action-btn" title="Editar" onclick="editarUbicacion(${ub.id})"><i class="bi bi-pencil-fill"></i></button>
                    <button class="admin-action-btn danger" title="Eliminar" onclick="eliminarUbicacion(${ub.id})"><i class="bi bi-trash-fill"></i></button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function renderTablaEdificios() {
    const tbody = document.querySelector('.admin-table tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    allData.edificios.forEach(ed => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>
                <div class="table-row-name">
                    <div class="icon-box"><i class="bi bi-building"></i></div>
                    <div>
                        <div class="table-row-name-text">Edificio ${ed.codigo}</div>
                        <div class="table-row-name-meta">${ed.nombre}</div>
                    </div>
                </div>
            </td>
            <td><span class="tag">${ed.campus}</span></td>
            <td>${ed.pisos} piso(s)</td>
            <td>${ed.ubicaciones_count} ubicaciones</td>
            <td><span class="status-chip confirmed"><i class="bi bi-check-circle-fill"></i> Activo</span></td>
            <td>
                <div class="table-actions">
                    <button class="admin-action-btn" title="Ver"><i class="bi bi-eye-fill"></i></button>
                    <button class="admin-action-btn" title="Editar"><i class="bi bi-pencil-fill"></i></button>
                    <button class="admin-action-btn danger" title="Eliminar"><i class="bi bi-trash-fill"></i></button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function renderTablaCampus() {
    const tbody = document.querySelector('.admin-table tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    allData.campus.forEach(c => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>
                <div class="table-row-name">
                    <div class="icon-box icon-box-secondary"><i class="bi bi-buildings"></i></div>
                    <div>
                        <div class="table-row-name-text">${c.nombre}</div>
                        <div class="table-row-name-meta">${c.codigo}</div>
                    </div>
                </div>
            </td>
            <td>${c.direccion}</td>
            <td>${c.edificios_count} edificios</td>
            <td>${c.ubicaciones_count} ubicaciones</td>
            <td><span class="status-chip ${c.activo ? 'confirmed' : 'inactive'}"><i class="bi ${c.activo ? 'bi-check-circle-fill' : 'bi-x-circle-fill'}"></i> ${c.activo ? 'Activo' : 'Inactivo'}</span></td>
            <td>
                <div class="table-actions">
                    <button class="admin-action-btn" title="Ver"><i class="bi bi-eye-fill"></i></button>
                    <button class="admin-action-btn" title="Editar"><i class="bi bi-pencil-fill"></i></button>
                    <button class="admin-action-btn danger" title="Eliminar"><i class="bi bi-trash-fill"></i></button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function renderTablaUsuarios() {
    const tbody = document.querySelector('.admin-table tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    allData.usuarios.forEach(user => {
        const rol = user.perfil ? user.perfil.rol : (user.is_superuser ? 'Administrador' : 'Sin perfil');
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>
                <div class="table-row-name">
                    <div class="icon-box icon-box-dark"><i class="bi bi-person-circle"></i></div>
                    <div>
                        <div class="table-row-name-text">${user.email}</div>
                        <div class="table-row-name-meta">${user.perfil ? user.perfil.nombre_completo : user.username}</div>
                    </div>
                </div>
            </td>
            <td><span class="tag">${rol}</span></td>
            <td>${user.is_superuser ? 'Sí' : 'No'}</td>
            <td>${user.is_active ? 'Activo' : 'Inactivo'}</td>
            <td>${new Date(user.date_joined).toLocaleDateString()}</td>
            <td>
                <div class="table-actions">
                    <button class="admin-action-btn" title="Ver"><i class="bi bi-eye-fill"></i></button>
                    <button class="admin-action-btn" title="Editar"><i class="bi bi-pencil-fill"></i></button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// ============================================================
// ACCIONES CRUD
// ============================================================

function verUbicacion(id) {
    const ub = allData.ubicaciones.find(u => u.id === id);
    if (ub) {
        alert(`Ubicación: ${ub.nombre}\nTipo: ${ub.tipo}\nEdificio: ${ub.edificio}\nCapacidad: ${ub.capacidad}`);
    }
}

function editarUbicacion(id) {
    alert('Editar ubicación ' + id);
}

async function eliminarUbicacion(id) {
    if (!confirm('¿Estás seguro de que deseas eliminar esta ubicación?')) return;
    
    try {
        const res = await fetch(`/api/admin/ubicaciones/${id}/eliminar/`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' }
        });
        const json = await res.json();
        if (json.status === 'success') {
            alert('Ubicación eliminada');
            cargarUbicaciones();
        }
    } catch (e) {
        console.error('Error eliminando:', e);
    }
}

// ============================================================
// TABS
// ============================================================

function cambiarTab(tab) {
    currentTab = tab;
    
    // Actualizar clase active en botones
    document.querySelectorAll('.admin-tab').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Cargar datos según tab
    switch(tab) {
        case 'ubicaciones':
            cargarUbicaciones();
            break;
        case 'edificios':
            cargarEdificios();
            break;
        case 'campus':
            cargarCampus();
            break;
        case 'usuarios':
            cargarUsuarios();
            break;
    }
}

// ============================================================
// INICIALIZACIÓN
// ============================================================

function inicializarAdmin() {
    // Event listeners para tabs
    document.querySelectorAll('.admin-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            cambiarTab(this.textContent.toLowerCase().trim());
        });
    });
    
    // Botón de crear nueva ubicación
    const btnCrear = document.querySelector('.btn-action-primary');
    if (btnCrear) {
        btnCrear.addEventListener('click', function() {
            if (currentTab === 'ubicaciones') {
                mostrarModalCrearUbicacion();
            }
        });
    }
    
    // Cargar datos iniciales
    cargarStats();
    cargarTodosLosStats();
    cargarCampus();
    cargarEdificios();
    cargarUbicaciones();
    console.log('admin.js initialized');
}

// ============================================================
// MODAL CREAR UBICACIÓN
// ============================================================

function mostrarModalCrearUbicacion() {
    const modal = `
    <div class="modal-overlay">
        <div class="modal-content">
            <div class="modal-header">
                <h2>Crear nueva ubicación</h2>
                <button class="modal-close" onclick="cerrarModal()">&times;</button>
            </div>
            <form id="formCrearUbicacion" onsubmit="crearUbicacion(event)">
                <div class="form-group">
                    <label>Campus *</label>
                    <select name="campus_id" required>
                        <option value="">Selecciona campus</option>
                        ${allData.campus.map(c => `<option value="${c.id}">${c.nombre}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label>Edificio</label>
                    <select name="edificio_id" id="selectEdificio">
                        <option value="">Selecciona edificio (opcional)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Nombre *</label>
                    <input type="text" name="nombre" required>
                </div>
                <div class="form-group">
                    <label>Tipo *</label>
                    <select name="tipo" required>
                        <option value="">Selecciona tipo</option>
                        <option value="aula">Aula</option>
                        <option value="laboratorio">Laboratorio</option>
                        <option value="oficina">Oficina</option>
                        <option value="entrada">Entrada</option>
                        <option value="servicio">Servicio</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Código</label>
                    <input type="text" name="codigo">
                </div>
                <div class="form-group">
                    <label>Piso</label>
                    <input type="number" name="piso" min="0" value="0">
                </div>
                <div class="form-group">
                    <label>Capacidad</label>
                    <input type="number" name="capacidad" min="0" value="0">
                </div>
                <div class="form-group">
                    <label>Descripción</label>
                    <textarea name="descripcion"></textarea>
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" name="tiene_qr">
                        Generar código QR
                    </label>
                </div>
                <div class="form-actions">
                    <button type="button" class="btn-cancel" onclick="cerrarModal()">Cancelar</button>
                    <button type="submit" class="btn-submit">Crear ubicación</button>
                </div>
            </form>
        </div>
    </div>
    `;
    
    const container = document.createElement('div');
    container.innerHTML = modal;
    document.body.appendChild(container.firstElementChild);
    
    // Listener para cargar edificios según campus
    const selectCampus = document.querySelector('select[name="campus_id"]');
    const selectEdificio = document.querySelector('#selectEdificio');

    function updateCampusOptions() {
        if (!selectCampus) return;
        selectCampus.innerHTML = '<option value="">Selecciona campus</option>' + allData.campus.map(c => `<option value="${c.id}">${c.nombre}</option>`).join('');
    }

    if (allData.campus.length === 0) {
        // Cargar y luego actualizar opciones
        cargarCampus().then(() => updateCampusOptions()).catch(() => updateCampusOptions());
    } else {
        updateCampusOptions();
    }

    if (selectCampus) {
        selectCampus.addEventListener('change', function() {
            const campusId = this.value;
            selectEdificio.innerHTML = '<option value="">Selecciona edificio (opcional)</option>';
            
            if (campusId) {
                const edificios = allData.edificios.filter(e => e.campus_id === parseInt(campusId));
                selectEdificio.innerHTML += edificios.map(e => `<option value="${e.id}">${e.nombre} (${e.codigo})</option>`).join('');
            }
        });
    }
}

async function crearUbicacion(e) {
    e.preventDefault();
    
    const form = document.getElementById('formCrearUbicacion');
    const formData = new FormData(form);
    
    const data = {
        nombre: formData.get('nombre'),
        tipo: formData.get('tipo'),
        campus_id: parseInt(formData.get('campus_id')),
        edificio_id: formData.get('edificio_id') ? parseInt(formData.get('edificio_id')) : null,
        codigo: formData.get('codigo'),
        piso: parseInt(formData.get('piso')) || 0,
        capacidad: parseInt(formData.get('capacidad')) || 0,
        descripcion: formData.get('descripcion'),
        tiene_qr: formData.get('tiene_qr') ? true : false,
    };
    
    // Obtener CSRF token y enviarlo en encabezados (Django)
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const csrftoken = getCookie('csrftoken');

    try {
        const res = await fetch('/api/admin/ubicaciones/crear/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
            body: JSON.stringify(data)
        });
        const json = await res.json();
        
        if (json.status === 'success') {
            alert('Ubicación creada exitosamente');
            cerrarModal();
            cargarUbicaciones();
        } else {
            alert('Error: ' + json.message);
        }
    } catch (e) {
        console.error('Error:', e);
        alert('Error al crear ubicación');
    }
}

function cerrarModal() {
    const overlay = document.querySelector('.modal-overlay');
    if (overlay) overlay.remove();
}

function initAdmin() {
    inicializarAdmin();
    const heading = document.querySelector('.page-title h1');
    if (heading) {
        heading.textContent = 'QUE PEDO';
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAdmin);
} else {
    initAdmin();
}

// Render current page (client-side pagination)
function renderCurrentPage() {
    const start = (currentPage - 1) * PAGE_SIZE;
    const end = start + PAGE_SIZE;
    const pageItems = allData.ubicaciones.slice(start, end);
    renderTablaUbicaciones(pageItems);
    // actualizar info de 'Mostrando X-Y de Z'
    const info = document.querySelector('.pagination-info');
    if (info) {
        const from = totalUbicaciones === 0 ? 0 : start + 1;
        const to = Math.min(end, totalUbicaciones);
        info.innerHTML = `Mostrando <strong>${from}-${to}</strong> de <strong>${totalUbicaciones}</strong> ubicaciones`;
    }
}

function actualizarPaginacion(totalCount) {
    totalUbicaciones = totalCount || 0;
    const controls = document.querySelector('.pagination-controls');
    if (!controls) return;
    controls.innerHTML = '';
    const totalPages = Math.max(1, Math.ceil(totalUbicaciones / PAGE_SIZE));

    const prev = document.createElement('button');
    prev.className = 'pagination-btn';
    prev.innerHTML = '<i class="bi bi-chevron-left"></i>';
    prev.disabled = currentPage === 1;
    prev.addEventListener('click', () => changePage(currentPage - 1));
    controls.appendChild(prev);

    for (let p = 1; p <= totalPages; p++) {
        const btn = document.createElement('button');
        btn.className = 'pagination-btn' + (p === currentPage ? ' active' : '');
        btn.textContent = p;
        btn.addEventListener('click', () => changePage(p));
        controls.appendChild(btn);
    }

    const next = document.createElement('button');
    next.className = 'pagination-btn';
    next.innerHTML = '<i class="bi bi-chevron-right"></i>';
    next.disabled = currentPage === totalPages;
    next.addEventListener('click', () => changePage(currentPage + 1));
    controls.appendChild(next);
}

function changePage(page) {
    const totalPages = Math.max(1, Math.ceil(totalUbicaciones / PAGE_SIZE));
    if (page < 1) page = 1;
    if (page > totalPages) page = totalPages;
    currentPage = page;
    // actualizar botones activos
    document.querySelectorAll('.pagination-controls .pagination-btn').forEach(btn => btn.classList.remove('active'));
    const btns = Array.from(document.querySelectorAll('.pagination-controls .pagination-btn'))
        .filter(b => b.textContent && !isNaN(parseInt(b.textContent)));
    const activeBtn = btns.find(b => parseInt(b.textContent) === currentPage);
    if (activeBtn) activeBtn.classList.add('active');
    renderCurrentPage();
}