/**
 * editor.js
 *
 * Controlador del Editor Visual de Grafo de CampusGo.
 * Permite crear, conectar y eliminar nodos del grafo de rutas
 * con clics directamente sobre el mapa Leaflet.
 *
 * Modos:
 *   - navigate: explorar el grafo (click en nodo → popup con acciones)
 *   - create:   click en mapa → crear nodo nuevo
 *   - connect:  click en 2 nodos → crear arista entre ellos
 *   - delete:   click en nodo → eliminarlo (y sus conexiones)
 */

(function() {
    'use strict';

    const CFG = window.EDITOR_CONFIG;

    // ============================================================
    // ESTADO GLOBAL
    // ============================================================
    let mapa;
    let modo = 'navigate';
    let nodos = [];                  // datos de nodos cargados del API
    let aristas = [];                // datos de aristas cargadas del API
    let ubicacionesDisponibles = []; // ubicaciones del campus (para vincular)
    let tiposNodo = [];
    let tiposArista = [];

    let marcadoresNodos = {};        // {nodo_id: L.marker}
    let lineasAristas = {};          // {arista_id: L.polyline}
    let marcadoresUbicaciones = [];  // pines de ubicaciones (toggle)
    let mostrarUbicaciones = false;

    let nodoSeleccionado = null;     // para modo "connect"

    // Textos de ayuda por modo
    const HINTS = {
        navigate: 'Modo navegación: explora el grafo. Haz clic en un nodo para ver opciones.',
        create:   'Modo crear: haz clic en cualquier punto del mapa para crear un nodo.',
        connect:  'Modo conectar: selecciona el primer nodo, después el segundo, para crear una conexión.',
        delete:   'Modo eliminar: haz clic sobre un nodo para borrarlo (también borra sus conexiones).',
    };

    const HINTS_BANNER = {
        create:  'Haz clic en el mapa donde quieres crear un nodo',
        connect: 'Selecciona el primer nodo',
        delete:  'Haz clic en el nodo que quieres eliminar',
    };

    // ============================================================
    // INICIALIZACIÓN
    // ============================================================
    document.addEventListener('DOMContentLoaded', async () => {
        try {
            iniciarMapa();
            configurarModos();
            configurarHerramientas();
            await cargarDatos();
            ocultarLoading();
        } catch (e) {
            console.error('Error al inicializar editor:', e);
            mostrarToast('Error al cargar el editor', 'error');
        }
    });

    function ocultarLoading() {
        const loading = document.getElementById('editor-loading');
        if (loading) loading.style.display = 'none';
    }

    // ============================================================
    // MAPA
    // ============================================================
    function iniciarMapa() {
        mapa = L.map('editor-map', {
            zoomControl: false,
        }).setView(CFG.centro, 18);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap',
            maxZoom: 20,
        }).addTo(mapa);

        L.control.zoom({ position: 'topright' }).addTo(mapa);

        // Click en el mapa
        mapa.on('click', (e) => {
            if (modo === 'create') {
                abrirModalCrearNodo(e.latlng.lat, e.latlng.lng);
            }
        });
    }

    // ============================================================
    // CARGAR DATOS DEL SERVIDOR
    // ============================================================
    async function cargarDatos() {
        const resp = await fetch(CFG.urls.data, {
            credentials: 'same-origin',
        });
        if (!resp.ok) throw new Error('Error al cargar datos');
        const data = await resp.json();

        nodos = data.nodos;
        aristas = data.aristas;
        ubicacionesDisponibles = data.ubicaciones_disponibles;
        tiposNodo = data.tipos_nodo;
        tiposArista = data.tipos_arista;

        renderizarTodo();
    }

    function renderizarTodo() {
        // Limpiar marcadores existentes
        Object.values(marcadoresNodos).forEach(m => mapa.removeLayer(m));
        Object.values(lineasAristas).forEach(l => mapa.removeLayer(l));
        marcadoresNodos = {};
        lineasAristas = {};

        // Renderizar nodos
        nodos.forEach(n => agregarMarcadorNodo(n));

        // Renderizar aristas
        aristas.forEach(a => agregarLineaArista(a));

        // Listas laterales
        renderizarListaNodos();
        renderizarListaAristas();

        // Stats
        actualizarStats();
    }

    function actualizarStats() {
        document.getElementById('stat-nodos').textContent = nodos.length;
        document.getElementById('stat-aristas').textContent = aristas.length;
        document.getElementById('count-nodos').textContent = nodos.length;
        document.getElementById('count-aristas').textContent = aristas.length;
    }

    // ============================================================
    // RENDERIZAR NODOS EN EL MAPA
    // ============================================================
    function agregarMarcadorNodo(nodo) {
        const marcador = L.marker([nodo.lat, nodo.lng], {
            icon: crearIconoNodo(nodo.tipo),
            draggable: false,
        });

        marcador.on('click', () => onClickNodo(nodo));
        marcador.addTo(mapa);
        marcadoresNodos[nodo.id] = marcador;
    }

    function crearIconoNodo(tipo, opciones = {}) {
        const iconosTipo = {
            entrada:  'bi-door-open-fill',
            pasillo:  'bi-circle-fill',
            cruce:    'bi-x-diamond-fill',
            plaza:    'bi-circle-square',
            edificio: 'bi-building-fill',
            escalera: 'bi-stairs',
        };
        const icon = iconosTipo[tipo] || 'bi-geo-alt-fill';

        let classes = `editor-pin ${tipo}`;
        if (opciones.selected) classes += ' selected';
        if (opciones.connecting) classes += ' connecting';

        return L.divIcon({
            className: '',
            html: `<div class="${classes}"><i class="bi ${icon}"></i></div>`,
            iconSize: [28, 28],
            iconAnchor: [14, 28],
            popupAnchor: [0, -28],
        });
    }

    function actualizarIconoNodo(nodoId, opciones = {}) {
        const nodo = nodos.find(n => n.id === nodoId);
        if (!nodo || !marcadoresNodos[nodoId]) return;
        marcadoresNodos[nodoId].setIcon(crearIconoNodo(nodo.tipo, opciones));
    }

    // ============================================================
    // RENDERIZAR ARISTAS EN EL MAPA
    // ============================================================
    function agregarLineaArista(arista) {
        const nodoOrigen = nodos.find(n => n.id === arista.origen_id);
        const nodoDestino = nodos.find(n => n.id === arista.destino_id);
        if (!nodoOrigen || !nodoDestino) return;

        const color = arista.accesible ? '#0E9E8E' : '#E8721C';

        const linea = L.polyline(
            [[nodoOrigen.lat, nodoOrigen.lng], [nodoDestino.lat, nodoDestino.lng]],
            {
                color: color,
                weight: 4,
                opacity: 0.75,
                dashArray: arista.tipo === 'escalera' ? '6, 8' : null,
            }
        );

        linea.bindTooltip(
            `${nodoOrigen.nombre} ↔ ${nodoDestino.nombre}<br>${arista.distancia_m}m`,
            { sticky: true, direction: 'top' }
        );

        linea.on('click', () => {
            if (modo === 'delete') {
                confirmarEliminarArista(arista);
            } else {
                mostrarToast(`Conexión: ${nodoOrigen.nombre} ↔ ${nodoDestino.nombre} (${arista.distancia_m}m)`, 'info');
            }
        });

        linea.addTo(mapa);
        lineasAristas[arista.id] = linea;
    }

    // ============================================================
    // CLICK EN NODO (según el modo)
    // ============================================================
    function onClickNodo(nodo) {
        if (modo === 'navigate') {
            abrirPopupNodo(nodo);
        } else if (modo === 'connect') {
            seleccionarParaConectar(nodo);
        } else if (modo === 'delete') {
            confirmarEliminarNodo(nodo);
        } else if (modo === 'create') {
            mostrarToast('Para crear un nodo, haz clic en una zona vacía del mapa.', 'warning');
        }
    }

    // ============================================================
    // POPUP DEL NODO (modo navigate)
    // ============================================================
    function abrirPopupNodo(nodo) {
        const marcador = marcadoresNodos[nodo.id];
        if (!marcador) return;

        const ubicacionTexto = nodo.ubicacion_nombre
            ? `<div style="font-size:11px; color:#0E9E8E; margin-top:4px;">
                 <i class="bi bi-link-45deg"></i> ${nodo.ubicacion_nombre}
               </div>`
            : '<div style="font-size:11px; color:#888; margin-top:4px;">Sin vincular</div>';

        const html = `
            <div style="font-weight:800; color:#1a2e35; font-size:14px;">${nodo.nombre}</div>
            <div style="font-size:12px; color:#888; font-weight:600;">${nodo.tipo_label}</div>
            ${ubicacionTexto}
            <div class="popup-actions">
                <button class="popup-btn" onclick="window.editorAcciones.editarNodo(${nodo.id})">
                    <i class="bi bi-pencil"></i> Editar
                </button>
                <button class="popup-btn danger" onclick="window.editorAcciones.eliminarNodo(${nodo.id})">
                    <i class="bi bi-trash"></i> Eliminar
                </button>
            </div>
        `;

        marcador.bindPopup(html).openPopup();
    }

    // ============================================================
    // CREAR NODO
    // ============================================================
    function abrirModalCrearNodo(lat, lng) {
        // Filtrar ubicaciones que aún no tienen nodo
        const disponibles = ubicacionesDisponibles.filter(u => !u.tiene_nodo);

        const optionsTipo = tiposNodo.map(t =>
            `<option value="${t.value}" ${t.value === 'pasillo' ? 'selected' : ''}>${t.label}</option>`
        ).join('');

        const optionsUbic = disponibles.length === 0
            ? '<option value="">(No hay ubicaciones disponibles)</option>'
            : '<option value="">— Sin vincular —</option>' +
              disponibles.map(u =>
                  `<option value="${u.id}">${u.nombre} (${u.tipo_label})</option>`
              ).join('');

        abrirModal({
            titulo: 'Crear nodo nuevo',
            subtitulo: `Coordenadas: ${lat.toFixed(6)}, ${lng.toFixed(6)}`,
            campos: `
                <div class="modal-field">
                    <label class="modal-label">Nombre del nodo</label>
                    <input class="modal-input" id="campo-nombre" placeholder="Ej. Plaza central" autofocus>
                </div>
                <div class="modal-field">
                    <label class="modal-label">Tipo</label>
                    <select class="modal-select" id="campo-tipo">${optionsTipo}</select>
                </div>
                <div class="modal-field">
                    <label class="modal-label">Vincular a ubicación (opcional)</label>
                    <select class="modal-select" id="campo-ubicacion">${optionsUbic}</select>
                </div>
            `,
            botonPrimario: 'Crear nodo',
            onConfirmar: async () => {
                const nombre = document.getElementById('campo-nombre').value.trim();
                const tipo = document.getElementById('campo-tipo').value;
                const ubicacionIdRaw = document.getElementById('campo-ubicacion').value;
                const ubicacionId = ubicacionIdRaw ? parseInt(ubicacionIdRaw) : null;

                if (!nombre) {
                    mostrarToast('El nombre es obligatorio', 'warning');
                    return false;
                }

                try {
                    const resp = await fetchJSON(CFG.urls.crearNodo, 'POST', {
                        lat, lng, nombre, tipo, ubicacion_id: ubicacionId,
                    });
                    nodos.push(resp.nodo);
                    // Si vinculó, marcar la ubicación como ocupada
                    if (ubicacionId) {
                        const u = ubicacionesDisponibles.find(x => x.id === ubicacionId);
                        if (u) u.tiene_nodo = true;
                    }
                    agregarMarcadorNodo(resp.nodo);
                    renderizarListaNodos();
                    actualizarStats();
                    mostrarToast(`Nodo "${nombre}" creado`, 'success');
                    return true;
                } catch (err) {
                    mostrarToast(err.message || 'Error al crear nodo', 'error');
                    return false;
                }
            },
        });
    }

    // ============================================================
    // EDITAR NODO
    // ============================================================
    function editarNodo(nodoId) {
        const nodo = nodos.find(n => n.id === nodoId);
        if (!nodo) return;
        cerrarPopupActivo();

        // Filtrar ubicaciones: las disponibles + la vinculada actualmente
        const disponibles = ubicacionesDisponibles.filter(
            u => !u.tiene_nodo || u.id === nodo.ubicacion_id
        );

        const optionsTipo = tiposNodo.map(t =>
            `<option value="${t.value}" ${t.value === nodo.tipo ? 'selected' : ''}>${t.label}</option>`
        ).join('');

        const optionsUbic = '<option value="">— Sin vincular —</option>' +
            disponibles.map(u =>
                `<option value="${u.id}" ${u.id === nodo.ubicacion_id ? 'selected' : ''}>${u.nombre} (${u.tipo_label})</option>`
            ).join('');

        abrirModal({
            titulo: 'Editar nodo',
            subtitulo: `ID: ${nodo.codigo}`,
            campos: `
                <div class="modal-field">
                    <label class="modal-label">Nombre</label>
                    <input class="modal-input" id="campo-nombre" value="${escapeHtml(nodo.nombre)}">
                </div>
                <div class="modal-field">
                    <label class="modal-label">Tipo</label>
                    <select class="modal-select" id="campo-tipo">${optionsTipo}</select>
                </div>
                <div class="modal-field">
                    <label class="modal-label">Vincular a ubicación</label>
                    <select class="modal-select" id="campo-ubicacion">${optionsUbic}</select>
                </div>
            `,
            botonPrimario: 'Guardar cambios',
            onConfirmar: async () => {
                const nombre = document.getElementById('campo-nombre').value.trim();
                const tipo = document.getElementById('campo-tipo').value;
                const ubicacionIdRaw = document.getElementById('campo-ubicacion').value;
                const ubicacionId = ubicacionIdRaw ? parseInt(ubicacionIdRaw) : null;

                if (!nombre) {
                    mostrarToast('El nombre es obligatorio', 'warning');
                    return false;
                }

                try {
                    const url = CFG.urls.actualizarNodo.replace('__ID__', nodoId);
                    const resp = await fetchJSON(url, 'POST', {
                        nombre, tipo, ubicacion_id: ubicacionId,
                    });

                    // Liberar/ocupar las ubicaciones según el cambio
                    if (nodo.ubicacion_id && nodo.ubicacion_id !== ubicacionId) {
                        const vieja = ubicacionesDisponibles.find(x => x.id === nodo.ubicacion_id);
                        if (vieja) vieja.tiene_nodo = false;
                    }
                    if (ubicacionId && ubicacionId !== nodo.ubicacion_id) {
                        const nueva = ubicacionesDisponibles.find(x => x.id === ubicacionId);
                        if (nueva) nueva.tiene_nodo = true;
                    }

                    // Actualizar los datos locales
                    Object.assign(nodo, resp.nodo);
                    actualizarIconoNodo(nodoId);
                    renderizarListaNodos();
                    mostrarToast('Nodo actualizado', 'success');
                    return true;
                } catch (err) {
                    mostrarToast(err.message || 'Error al actualizar', 'error');
                    return false;
                }
            },
        });
    }

    // ============================================================
    // ELIMINAR NODO
    // ============================================================
    function confirmarEliminarNodo(nodo) {
        cerrarPopupActivo();
        const conexiones = aristas.filter(
            a => a.origen_id === nodo.id || a.destino_id === nodo.id
        ).length;

        const aviso = conexiones > 0
            ? `<div style="background:#fff3cd; color:#8a6b00; padding:10px; border-radius:8px; font-size:12px; font-weight:700;">
                 ⚠️ Esto también eliminará ${conexiones} conexión(es) asociada(s).
               </div>`
            : '';

        abrirModal({
            titulo: '¿Eliminar este nodo?',
            subtitulo: `"${nodo.nombre}" se borrará permanentemente.`,
            campos: aviso,
            botonPrimario: 'Eliminar',
            esDanger: true,
            onConfirmar: async () => {
                try {
                    const url = CFG.urls.eliminarNodo.replace('__ID__', nodo.id);
                    await fetchJSON(url, 'POST');

                    // Quitar del mapa y de los datos
                    mapa.removeLayer(marcadoresNodos[nodo.id]);
                    delete marcadoresNodos[nodo.id];

                    // Eliminar también las aristas que tocaban el nodo
                    const aristasABorrar = aristas.filter(
                        a => a.origen_id === nodo.id || a.destino_id === nodo.id
                    );
                    aristasABorrar.forEach(a => {
                        if (lineasAristas[a.id]) {
                            mapa.removeLayer(lineasAristas[a.id]);
                            delete lineasAristas[a.id];
                        }
                    });
                    aristas = aristas.filter(
                        a => a.origen_id !== nodo.id && a.destino_id !== nodo.id
                    );

                    // Liberar la ubicación si estaba vinculada
                    if (nodo.ubicacion_id) {
                        const u = ubicacionesDisponibles.find(x => x.id === nodo.ubicacion_id);
                        if (u) u.tiene_nodo = false;
                    }

                    nodos = nodos.filter(n => n.id !== nodo.id);
                    renderizarListaNodos();
                    renderizarListaAristas();
                    actualizarStats();
                    mostrarToast(`Nodo "${nodo.nombre}" eliminado`, 'success');
                    return true;
                } catch (err) {
                    mostrarToast(err.message || 'Error al eliminar', 'error');
                    return false;
                }
            },
        });
    }

    // ============================================================
    // CONECTAR DOS NODOS
    // ============================================================
    function seleccionarParaConectar(nodo) {
        if (!nodoSeleccionado) {
            // Primer nodo
            nodoSeleccionado = nodo;
            actualizarIconoNodo(nodo.id, { connecting: true });
            actualizarBannerHint(`Primer nodo: ${nodo.nombre}. Selecciona el segundo para conectar.`);
            return;
        }

        if (nodoSeleccionado.id === nodo.id) {
            // Mismo nodo → cancelar selección
            actualizarIconoNodo(nodo.id);
            nodoSeleccionado = null;
            actualizarBannerHint(HINTS_BANNER.connect);
            return;
        }

        // Segundo nodo: abrir modal para confirmar
        abrirModalCrearArista(nodoSeleccionado, nodo);
    }

    function abrirModalCrearArista(origen, destino) {
        const optionsTipo = tiposArista.map(t =>
            `<option value="${t.value}" ${t.value === 'sendero' ? 'selected' : ''}>${t.label}</option>`
        ).join('');

        abrirModal({
            titulo: 'Crear conexión',
            subtitulo: `${origen.nombre} ↔ ${destino.nombre}`,
            campos: `
                <div class="modal-field">
                    <label class="modal-label">Tipo de camino</label>
                    <select class="modal-select" id="campo-tipo">${optionsTipo}</select>
                </div>
                <div class="modal-field">
                    <label class="modal-checkbox-row">
                        <input type="checkbox" id="campo-accesible" checked>
                        Es accesible para silla de ruedas
                    </label>
                </div>
                <div class="modal-field">
                    <label class="modal-checkbox-row">
                        <input type="checkbox" id="campo-bidireccional" checked>
                        Bidireccional (se puede ir y volver)
                    </label>
                </div>
                <div style="font-size:11px; color:#888; font-weight:600; margin-top:8px;">
                    <i class="bi bi-info-circle"></i> La distancia se calcula automáticamente.
                </div>
            `,
            botonPrimario: 'Crear conexión',
            onConfirmar: async () => {
                const tipo = document.getElementById('campo-tipo').value;
                const accesible = document.getElementById('campo-accesible').checked;
                const bidireccional = document.getElementById('campo-bidireccional').checked;

                try {
                    const resp = await fetchJSON(CFG.urls.crearArista, 'POST', {
                        origen_id: origen.id,
                        destino_id: destino.id,
                        tipo, accesible, bidireccional,
                    });
                    aristas.push(resp.arista);
                    agregarLineaArista(resp.arista);
                    renderizarListaAristas();
                    actualizarStats();
                    mostrarToast(`Conexión creada (${resp.arista.distancia_m}m)`, 'success');

                    // Limpiar selección
                    actualizarIconoNodo(origen.id);
                    nodoSeleccionado = null;
                    actualizarBannerHint(HINTS_BANNER.connect);
                    return true;
                } catch (err) {
                    mostrarToast(err.message || 'Error al crear conexión', 'error');
                    return false;
                }
            },
            onCancelar: () => {
                actualizarIconoNodo(origen.id);
                nodoSeleccionado = null;
                actualizarBannerHint(HINTS_BANNER.connect);
            }
        });
    }

    // ============================================================
    // ELIMINAR ARISTA
    // ============================================================
    function confirmarEliminarArista(arista) {
        abrirModal({
            titulo: '¿Eliminar esta conexión?',
            subtitulo: `${arista.origen_nombre} ↔ ${arista.destino_nombre} (${arista.distancia_m}m)`,
            campos: '',
            botonPrimario: 'Eliminar',
            esDanger: true,
            onConfirmar: async () => {
                try {
                    const url = CFG.urls.eliminarArista.replace('__ID__', arista.id);
                    await fetchJSON(url, 'POST');
                    if (lineasAristas[arista.id]) {
                        mapa.removeLayer(lineasAristas[arista.id]);
                        delete lineasAristas[arista.id];
                    }
                    aristas = aristas.filter(a => a.id !== arista.id);
                    renderizarListaAristas();
                    actualizarStats();
                    mostrarToast('Conexión eliminada', 'success');
                    return true;
                } catch (err) {
                    mostrarToast(err.message || 'Error al eliminar', 'error');
                    return false;
                }
            },
        });
    }

    // ============================================================
    // LISTAS LATERALES
    // ============================================================
    function renderizarListaNodos() {
        const cont = document.getElementById('lista-nodos');
        if (nodos.length === 0) {
            cont.innerHTML = '<div class="empty-list">Aún no hay nodos. Cambia a "Crear nodo" y haz clic en el mapa.</div>';
            return;
        }

        cont.innerHTML = nodos.map(n => {
            const vinculo = n.ubicacion_nombre
                ? `<i class="bi bi-link-45deg" style="color:#0E9E8E;"></i> ${escapeHtml(n.ubicacion_nombre)}`
                : n.tipo_label;
            return `
                <div class="element-item" data-id="${n.id}">
                    <div class="element-icon ${n.tipo}">
                        <i class="bi ${iconoPorTipo(n.tipo)}"></i>
                    </div>
                    <div class="element-info">
                        <div class="element-name">${escapeHtml(n.nombre)}</div>
                        <div class="element-meta">${vinculo}</div>
                    </div>
                </div>
            `;
        }).join('');

        // Click en item: centrar mapa y abrir popup
        cont.querySelectorAll('.element-item').forEach(item => {
            item.addEventListener('click', () => {
                const id = parseInt(item.dataset.id);
                const nodo = nodos.find(n => n.id === id);
                if (nodo) {
                    mapa.flyTo([nodo.lat, nodo.lng], 19, { duration: 0.6 });
                    setTimeout(() => abrirPopupNodo(nodo), 700);
                }
            });
        });
    }

    function renderizarListaAristas() {
        const cont = document.getElementById('lista-aristas');
        if (aristas.length === 0) {
            cont.innerHTML = '<div class="empty-list">Aún no hay conexiones.</div>';
            return;
        }

        cont.innerHTML = aristas.map(a => `
            <div class="element-item" data-id="${a.id}">
                <div class="element-icon">
                    <i class="bi bi-share-fill"></i>
                </div>
                <div class="element-info">
                    <div class="element-name">${escapeHtml(a.origen_nombre)} ↔ ${escapeHtml(a.destino_nombre)}</div>
                    <div class="element-meta">${a.distancia_m}m · ${a.tipo_label}${a.accesible ? '' : ' · ⚠️ No accesible'}</div>
                </div>
            </div>
        `).join('');
    }

    function iconoPorTipo(tipo) {
        const map = {
            entrada: 'bi-door-open-fill',
            pasillo: 'bi-circle-fill',
            cruce: 'bi-x-diamond-fill',
            plaza: 'bi-circle-square',
            edificio: 'bi-building-fill',
            escalera: 'bi-stairs',
        };
        return map[tipo] || 'bi-geo-alt-fill';
    }

    // ============================================================
    // MODOS DE EDICIÓN
    // ============================================================
    function configurarModos() {
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                cambiarModo(btn.dataset.mode);
            });
        });
    }

    function cambiarModo(nuevoModo) {
        // Limpiar selección de conexión si la hay
        if (modo === 'connect' && nodoSeleccionado) {
            actualizarIconoNodo(nodoSeleccionado.id);
            nodoSeleccionado = null;
        }

        modo = nuevoModo;

        // UI: botones activos
        document.querySelectorAll('.mode-btn').forEach(b => {
            b.classList.toggle('active', b.dataset.mode === nuevoModo);
        });

        // Cursor del mapa
        const container = document.getElementById('map-container');
        container.className = 'editor-map-container ' + 'mode-' + nuevoModo;

        // Texto de hint
        document.getElementById('mode-hint-text').textContent = HINTS[nuevoModo];

        // Banner flotante sobre el mapa
        if (HINTS_BANNER[nuevoModo]) {
            mostrarBannerHint(HINTS_BANNER[nuevoModo]);
        } else {
            ocultarBannerHint();
        }

        cerrarPopupActivo();
    }

    function mostrarBannerHint(texto) {
        const cont = document.getElementById('hint-banner-container');
        cont.innerHTML = `
            <div class="editor-hint-banner">
                <i class="bi bi-info-circle-fill"></i>
                <span>${escapeHtml(texto)}</span>
            </div>
        `;
    }

    function actualizarBannerHint(texto) {
        mostrarBannerHint(texto);
    }

    function ocultarBannerHint() {
        document.getElementById('hint-banner-container').innerHTML = '';
    }

    // ============================================================
    // HERRAMIENTAS
    // ============================================================
    function configurarHerramientas() {
        document.getElementById('btn-centrar').addEventListener('click', () => {
            if (nodos.length === 0) {
                mapa.flyTo(CFG.centro, 18, { duration: 0.8 });
            } else {
                const bounds = L.latLngBounds(nodos.map(n => [n.lat, n.lng]));
                mapa.flyToBounds(bounds, { padding: [60, 60], duration: 0.8 });
            }
        });

        document.getElementById('btn-ver-ubicaciones').addEventListener('click', toggleUbicaciones);
    }

    function toggleUbicaciones() {
        mostrarUbicaciones = !mostrarUbicaciones;
        const btn = document.getElementById('btn-ver-ubicaciones');

        if (mostrarUbicaciones) {
            // Cargar pines de las ubicaciones desde el API público
            fetch(`/api/campus/${CFG.campusCodigo}/ubicaciones/`)
                .then(r => r.json())
                .then(data => {
                    data.ubicaciones.forEach(u => {
                        const m = L.marker([u.lat, u.lng], {
                            icon: L.divIcon({
                                className: '',
                                html: `<div style="background:#fff; border:2px solid #E8721C; width:12px; height:12px; border-radius:50%;"></div>`,
                                iconSize: [12, 12],
                                iconAnchor: [6, 6],
                            }),
                            opacity: 0.8,
                        });
                        m.bindTooltip(`📍 ${u.nombre}`, { direction: 'top' });
                        m.addTo(mapa);
                        marcadoresUbicaciones.push(m);
                    });
                    btn.innerHTML = '<i class="bi bi-eye-slash-fill"></i> Ocultar ubicaciones';
                    mostrarToast(`${data.ubicaciones.length} ubicaciones mostradas`, 'info');
                });
        } else {
            marcadoresUbicaciones.forEach(m => mapa.removeLayer(m));
            marcadoresUbicaciones = [];
            btn.innerHTML = '<i class="bi bi-geo-alt-fill"></i> Mostrar ubicaciones (QR)';
        }
    }

    // ============================================================
    // MODAL
    // ============================================================
    function abrirModal({ titulo, subtitulo, campos, botonPrimario, esDanger = false, onConfirmar, onCancelar }) {
        const cont = document.getElementById('modal-container');
        const btnClass = esDanger ? 'modal-btn modal-btn-danger' : 'modal-btn modal-btn-primary';

        cont.innerHTML = `
            <div class="modal-backdrop" id="modal-backdrop">
                <div class="modal-card" onclick="event.stopPropagation()">
                    <div class="modal-title">${escapeHtml(titulo)}</div>
                    ${subtitulo ? `<div class="modal-subtitle">${escapeHtml(subtitulo)}</div>` : ''}
                    ${campos}
                    <div class="modal-actions">
                        <button class="modal-btn modal-btn-cancel" id="modal-cancelar">Cancelar</button>
                        <button class="${btnClass}" id="modal-confirmar">${botonPrimario}</button>
                    </div>
                </div>
            </div>
        `;

        const cerrar = () => { cont.innerHTML = ''; };

        document.getElementById('modal-cancelar').addEventListener('click', () => {
            if (onCancelar) onCancelar();
            cerrar();
        });

        document.getElementById('modal-backdrop').addEventListener('click', () => {
            if (onCancelar) onCancelar();
            cerrar();
        });

        document.getElementById('modal-confirmar').addEventListener('click', async () => {
            const ok = await onConfirmar();
            if (ok) cerrar();
        });

        // Enter para confirmar
        const primerInput = cont.querySelector('input, select');
        if (primerInput) primerInput.focus();
    }

    function cerrarPopupActivo() {
        mapa.closePopup();
    }

    // ============================================================
    // TOASTS
    // ============================================================
    function mostrarToast(mensaje, tipo = 'info', duracion = 3500) {
        const cont = document.getElementById('toast-container');
        const iconos = {
            success: 'bi-check-circle-fill',
            error:   'bi-x-circle-fill',
            warning: 'bi-exclamation-triangle-fill',
            info:    'bi-info-circle-fill',
        };

        const toast = document.createElement('div');
        toast.className = `toast ${tipo}`;
        toast.innerHTML = `<i class="bi ${iconos[tipo] || iconos.info}"></i><span>${escapeHtml(mensaje)}</span>`;
        cont.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(20px)';
            setTimeout(() => toast.remove(), 300);
        }, duracion);
    }

    // ============================================================
    // UTILIDADES
    // ============================================================
    async function fetchJSON(url, method = 'GET', body = null) {
        const opts = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CFG.csrfToken,
            },
            credentials: 'same-origin',
        };
        if (body) opts.body = JSON.stringify(body);

        const resp = await fetch(url, opts);
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.error || `HTTP ${resp.status}`);
        return data;
    }

    function escapeHtml(str) {
        if (str == null) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // ============================================================
    // ACCIONES GLOBALES (para llamar desde popups inline)
    // ============================================================
    window.editorAcciones = {
        editarNodo: function(id) { editarNodo(id); },
        eliminarNodo: function(id) {
            const nodo = nodos.find(n => n.id === id);
            if (nodo) confirmarEliminarNodo(nodo);
        },
    };
})();