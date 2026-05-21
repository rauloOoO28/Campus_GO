document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form');
    if (!form) return;

    const nombre = document.getElementById('id_nombre_completo');
    const email = document.getElementById('id_email');
    const role = document.getElementById('id_rol');
    const pwd1 = document.getElementById('id_password');
    const pwd2 = document.getElementById('id_password2');

    function showError(input, msg) {
        clearError(input);
        const span = document.createElement('div');
        span.className = 'field-error';
        span.style.color = 'var(--color-danger, #c0392b)';
        span.style.fontSize = '13px';
        span.style.marginTop = '6px';
        span.textContent = msg;
        input.closest('.login-form-input-wrapper').after(span);
        input.classList.add('input-error');
    }

    function clearError(input) {
        const wrapper = input.closest('.login-form-input-wrapper');
        if (!wrapper) return;
        const next = wrapper.nextElementSibling;
        if (next && next.classList.contains('field-error')) next.remove();
        input.classList.remove('input-error');
    }

    function startsWithDoubleSpace(val) {
        return val.startsWith('  ');
    }

    function validateNombre() {
        const val = nombre.value || '';
        if (!val.trim()) { showError(nombre, 'El nombre es obligatorio.'); return false; }
        if (startsWithDoubleSpace(val)) { showError(nombre, 'No debe iniciar con doble espacio.'); return false; }
        if (val.length > 60) { showError(nombre, 'Máximo 60 caracteres permitidos.'); return false; }
        const nameRegex = /^[A-Za-zÀ-ÿ\s]+$/u;
        if (!nameRegex.test(val)) { showError(nombre, 'Solo letras y espacios son permitidos.'); return false; }
        clearError(nombre); return true;
    }

    function validateEmail() {
        const val = email.value || '';
        if (!val.trim()) { showError(email, 'El correo es obligatorio.'); return false; }
        if (startsWithDoubleSpace(val)) { showError(email, 'No debe iniciar con doble espacio.'); return false; }
        if (val.length > 40) { showError(email, 'Máximo 40 caracteres permitidos.'); return false; }
        if (!val.includes('@')) { showError(email, 'El correo debe contener "@".'); return false; }
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(val)) { showError(email, 'Correo no tiene un formato válido.'); return false; }
        clearError(email); return true;
    }

    function validateRole() {
        const val = role.value || '';
        if (!val) { showError(role, 'Selecciona tu rol.'); return false; }
        clearError(role); return true;
    }

    function validatePassword() {
        const val = pwd1.value || '';
        if (!val) { showError(pwd1, 'La contraseña es obligatoria.'); return false; }
        if (startsWithDoubleSpace(val)) { showError(pwd1, 'No debe iniciar con doble espacio.'); return false; }
        if (val.length < 8) { showError(pwd1, 'La contraseña debe tener al menos 8 caracteres.'); return false; }
        const passRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/;
        if (!passRegex.test(val)) { showError(pwd1, 'Debe contener mayúscula, minúscula, número y caracter especial.'); return false; }
        clearError(pwd1); return true;
    }

    function showFormMessage(text) {
        const msg = document.getElementById('registro-message');
        if (!msg) return;
        if (!text) {
            msg.style.display = 'none';
            msg.textContent = '';
            return;
        }
        msg.style.display = 'block';
        msg.textContent = text;
    }

    function validatePasswordMatch() {
        const v1 = pwd1.value || '';
        const v2 = pwd2.value || '';
        if (!v2) { showError(pwd2, 'Confirma la contraseña.'); showFormMessage('Las contraseñas no coinciden.'); return false; }
        if (startsWithDoubleSpace(v2)) { showError(pwd2, 'No debe iniciar con doble espacio.'); showFormMessage('Las contraseñas no coinciden.'); return false; }
        if (v1 !== v2) { showError(pwd2, 'Las contraseñas no coinciden.'); showFormMessage('Las contraseñas no coinciden.'); return false; }
        clearError(pwd2);
        showFormMessage('');
        return true;
    }

    nombre && nombre.addEventListener('input', validateNombre);
    email && email.addEventListener('input', validateEmail);
    role && role.addEventListener('change', validateRole);
    pwd1 && pwd1.addEventListener('input', validatePassword);
    pwd2 && pwd2.addEventListener('input', validatePasswordMatch);

    form.addEventListener('submit', function (e) {
        const okName = validateNombre();
        const okEmail = validateEmail();
        const okRole = validateRole();
        const okPwd = validatePassword();
        const okMatch = validatePasswordMatch();
        if (!(okName && okEmail && okRole && okPwd && okMatch)) {
            e.preventDefault();
            const firstError = document.querySelector('.field-error');
            if (firstError) firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    });
});