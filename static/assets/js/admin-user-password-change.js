/**
 * SBOT - JavaScript para la página de cambio de contraseña
 * URL: http://192.168.30.241:8000/admin/auth/user/3/password/
 * Implementado por Claude - Mayo 2025
 */

document.addEventListener('DOMContentLoaded', function() {
    // Verificar si estamos en la página de cambio de contraseña
    const isPasswordChangePage = window.location.pathname.includes('/password/');
    
    if (!isPasswordChangePage) return;
    
    console.log('Inicializando mejoras para la página de cambio de contraseña');
    
    // Ocultar completamente la barra lateral
    hideNavbar();
    
    // Mejorar los elementos del formulario
    enhanceFormElements();
    
    // Añadir validación de contraseña
    addPasswordValidation();
    
    // Mejorar los títulos y mensajes
    enhanceTextElements();
    
    console.log('Mejoras para la página de cambio de contraseña aplicadas');
});

/**
 * Oculta la barra de navegación lateral
 */
function hideNavbar() {
    // Quitar la barra lateral
    const navbar = document.querySelector('.pcoded-navbar');
    if (navbar) {
        navbar.style.display = 'none';
        navbar.style.width = '0';
        navbar.style.position = 'absolute';
        navbar.style.left = '-9999px';
    }
    
    // Ajustar el contenido principal para ocupar todo el ancho
    const mainContainer = document.querySelector('.pcoded-main-container');
    if (mainContainer) {
        mainContainer.style.marginLeft = '0';
        mainContainer.style.width = '100%';
    }
    
    // Asegurar que el contenido esté a todo el ancho
    const content = document.querySelector('.pcoded-content');
    if (content) {
        content.style.marginLeft = '0';
        content.style.width = '100%';
    }
    
    // Añadir clase al body para identificar esta página
    document.body.classList.add('password-change-page');
    
    // Forzar fondo blanco en todo el contenedor
    document.querySelectorAll('.pcoded-main-container, .pcoded-content, body').forEach(el => {
        el.style.backgroundColor = 'white';
    });
}

/**
 * Mejora los elementos del formulario para una mejor apariencia
 */
function enhanceFormElements() {
    // Envolver elementos del formulario en contenedores mejorados
    const form = document.querySelector('form');
    if (!form) return;
    
    // Añadir clase al formulario
    form.classList.add('password-change-form');
    
    // Mejorar los campos de contraseña
    const passwordFields = form.querySelectorAll('input[type="password"]');
    passwordFields.forEach(field => {
        // Añadir clases y placeholders
        field.classList.add('enhanced-password-field');
        
        if (field.id === 'id_password1') {
            field.setAttribute('placeholder', 'Ingrese la nueva contraseña');
        } else if (field.id === 'id_password2') {
            field.setAttribute('placeholder', 'Confirme la nueva contraseña');
        }
        
        // Crear contenedor para elementos de contraseña
        const fieldContainer = field.closest('div, p');
        if (fieldContainer) {
            fieldContainer.classList.add('password-field-container');
        }
    });
    
    // Mejorar los textos de ayuda
    const helpTexts = form.querySelectorAll('.helptext, .help');
    helpTexts.forEach(help => {
        help.classList.add('enhanced-help');
    });
    
    // Mejorar los botones
    const submitButtons = form.querySelectorAll('input[type="submit"]');
    submitButtons.forEach(button => {
        button.classList.add('enhanced-button');
    });
}

/**
 * Añade validación de contraseña con indicador visual de fortaleza
 */
function addPasswordValidation() {
    const password1 = document.getElementById('id_password1');
    if (!password1) return;
    
    // Crear elementos para mostrar la fortaleza de la contraseña
    const container = document.createElement('div');
    container.className = 'password-strength-container';
    
    const meter = document.createElement('div');
    meter.className = 'password-strength-meter';
    const value = document.createElement('div');
    value.className = 'password-strength-value';
    meter.appendChild(value);
    
    const text = document.createElement('div');
    text.className = 'password-strength-text';
    text.innerHTML = '<span class="fortaleza-label">Fortaleza:</span><span class="strength-value-text vacio-label">Vacío</span>';
    
    container.appendChild(meter);
    container.appendChild(text);
    
    // Insertar después del campo de contraseña
    const fieldContainer = password1.closest('div, p');
    if (fieldContainer) {
        fieldContainer.appendChild(container);
    }
    
    // Actualizar la fortaleza cuando cambie la contraseña
    password1.addEventListener('input', function() {
        validatePasswordStrength(this.value, value, text);
    });
    
    // Validar coincidencia de contraseñas
    const password2 = document.getElementById('id_password2');
    if (password2) {
        password2.addEventListener('input', function() {
            validatePasswordMatch(password1, password2);
        });
    }
}

/**
 * Calcula y muestra la fortaleza de la contraseña
 */
function validatePasswordStrength(password, valueEl, textEl) {
    const strengthText = textEl.querySelector('.strength-value-text');
    
    // Si la contraseña está vacía
    if (!password) {
        valueEl.className = 'password-strength-value';
        strengthText.textContent = 'Vacío';
        strengthText.className = 'strength-value-text vacio-label';
        return;
    }
    
    // Calcular fortaleza
    let strength = 0;
    
    // Criterios de fortaleza
    if (password.length >= 8) strength += 1;
    if (/[A-Z]/.test(password)) strength += 1;
    if (/[0-9]/.test(password)) strength += 1;
    if (/[^a-zA-Z0-9]/.test(password)) strength += 1;
    
    // Actualizar el indicador visual
    valueEl.className = 'password-strength-value';
    strengthText.className = 'strength-value-text';
    
    switch (strength) {
        case 0:
        case 1:
            valueEl.classList.add('strength-weak');
            strengthText.textContent = 'Débil';
            strengthText.style.color = '#e74c3c';
            break;
        case 2:
            valueEl.classList.add('strength-medium');
            strengthText.textContent = 'Media';
            strengthText.style.color = '#f39c12';
            break;
        case 3:
            valueEl.classList.add('strength-good');
            strengthText.textContent = 'Buena';
            strengthText.style.color = '#2ecc71';
            break;
        case 4:
            valueEl.classList.add('strength-strong');
            strengthText.textContent = 'Fuerte';
            strengthText.style.color = '#27ae60';
            break;
    }
}

/**
 * Valida que las contraseñas coincidan
 */
function validatePasswordMatch(password1, password2) {
    // Eliminar mensaje de error previo
    const existingError = document.querySelector('.password-match-error');
    if (existingError) existingError.remove();
    
    // Solo validar si ambos campos tienen valor
    if (!password1.value || !password2.value) return;
    
    // Validar coincidencia
    if (password1.value !== password2.value) {
        // Crear mensaje de error
        const errorMsg = document.createElement('div');
        errorMsg.className = 'password-match-error';
        errorMsg.textContent = 'Las contraseñas no coinciden';
        errorMsg.style.color = '#e74c3c';
        errorMsg.style.marginTop = '5px';
        errorMsg.style.fontSize = '13px';
        
        // Añadir después del segundo campo de contraseña
        const containerField2 = password2.closest('div, p');
        if (containerField2) {
            containerField2.appendChild(errorMsg);
        }
    }
}

/**
 * Mejora los textos y títulos para mejor legibilidad
 */
function enhanceTextElements() {
    // Mejorar títulos
    const headings = document.querySelectorAll('h1, h2, h3');
    headings.forEach(heading => {
        heading.classList.add('enhanced-heading');
    });
    
    // Si no hay un título en la página, añadir uno
    const pageTitle = document.querySelector('h1, h2, h3');
    if (!pageTitle) {
        const title = document.createElement('h1');
        title.textContent = 'Cambiar contraseña';
        title.className = 'enhanced-heading';
        
        const content = document.querySelector('.pcoded-content');
        if (content) {
            content.insertBefore(title, content.firstChild);
        }
    }
}
