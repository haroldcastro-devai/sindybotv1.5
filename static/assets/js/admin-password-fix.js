/**
 * SBOT - JavaScript para corregir y mejorar la página de cambio de contraseña
 * URL: http://192.168.30.241:8000/admin/auth/user/3/password/
 */

document.addEventListener('DOMContentLoaded', function() {
    // Comprobar si estamos en la página de cambio de contraseña
    if (window.location.pathname.includes('/password/')) {
        console.log('Aplicando mejoras a la página de cambio de contraseña');
        
        // Añadir clase al body para identificar esta página
        document.body.classList.add('change-password');
        
        // Añadir placeholders a los campos de contraseña
        const passwordFields = document.querySelectorAll('input[type="password"]');
        if (passwordFields.length >= 2) {
            passwordFields[0].setAttribute('placeholder', 'Ingrese la nueva contraseña');
            passwordFields[1].setAttribute('placeholder', 'Confirme la nueva contraseña');
            
            // Añadir clase para mejorar los estilos
            passwordFields.forEach(field => {
                field.classList.add('password-field');
                
                // Aplicar estilos y funcionalidad a cada campo
                setupPasswordField(field);
            });
            
            // Añadir validación de fortaleza de contraseña
            setupPasswordStrength(passwordFields[0]);
            
            // Añadir validación de coincidencia de contraseñas
            setupPasswordMatch(passwordFields[0], passwordFields[1]);
        }
        
        // Mejorar campos de ayuda
        const helpTexts = document.querySelectorAll('.help, .helptext');
        helpTexts.forEach(helpText => {
            // Añadir icono informativo
            if (!helpText.querySelector('.help-icon')) {
                const icon = document.createElement('span');
                icon.className = 'help-icon';
                icon.textContent = 'ℹ️ ';
                helpText.insertBefore(icon, helpText.firstChild);
            }
        });
        
        // Mejorar botones de envío
        const submitButtons = document.querySelectorAll('input[type="submit"], button[type="submit"]');
        submitButtons.forEach(button => {
            button.classList.add('submit-button');
        });
        
        // Reorganizar el formulario para mejor estructura
        reorganizeForm();
    }
});

/**
 * Configura un campo de contraseña con mejor UX
 */
function setupPasswordField(field) {
    // Envolver el campo en un contenedor para posicionamiento relativo
    const wrapper = document.createElement('div');
    wrapper.className = 'password-field-container';
    
    // Insertar el wrapper antes del campo
    field.parentNode.insertBefore(wrapper, field);
    
    // Mover el campo dentro del wrapper
    wrapper.appendChild(field);
    
    // Añadir botón para mostrar/ocultar contraseña
    const toggleButton = document.createElement('button');
    toggleButton.type = 'button';
    toggleButton.className = 'password-toggle';
    toggleButton.textContent = '👁️';
    toggleButton.title = 'Mostrar/Ocultar contraseña';
    toggleButton.style.position = 'absolute';
    toggleButton.style.right = '10px';
    toggleButton.style.top = '50%';
    toggleButton.style.transform = 'translateY(-50%)';
    toggleButton.style.background = 'none';
    toggleButton.style.border = 'none';
    toggleButton.style.cursor = 'pointer';
    toggleButton.style.fontSize = '16px';
    toggleButton.style.color = '#95a5a6';
    
    // Añadir el botón después del campo
    wrapper.appendChild(toggleButton);
    
    // Configurar funcionalidad del botón
    toggleButton.addEventListener('click', function() {
        const type = field.getAttribute('type') === 'password' ? 'text' : 'password';
        field.setAttribute('type', type);
        this.textContent = type === 'password' ? '👁️' : '👁️‍🗨️';
    });
    
    // Añadir clase focused al wrapper cuando el campo tiene focus
    field.addEventListener('focus', function() {
        wrapper.classList.add('focused');
    });
    
    field.addEventListener('blur', function() {
        wrapper.classList.remove('focused');
    });
}

/**
 * Configura el indicador de fortaleza de contraseña
 */
function setupPasswordStrength(passwordField) {
    // Crear contenedor para el indicador de fortaleza
    const strengthContainer = document.createElement('div');
    strengthContainer.className = 'password-strength';
    
    // Crear barra de fortaleza
    const strengthBar = document.createElement('div');
    strengthBar.className = 'password-strength-bar';
    
    // Crear relleno de la barra
    const strengthFill = document.createElement('div');
    strengthFill.className = 'password-strength-value';
    strengthBar.appendChild(strengthFill);
    
    // Crear texto de fortaleza
    const strengthText = document.createElement('div');
    strengthText.className = 'fortaleza';
    strengthText.innerHTML = '<span class="fortaleza-label">Fortaleza:</span><span class="fortaleza-value">Vacío</span>';
    
    // Añadir elementos al contenedor
    strengthContainer.appendChild(strengthBar);
    strengthContainer.appendChild(strengthText);
    
    // Insertar después del campo de contraseña
    const wrapper = passwordField.closest('.password-field-container');
    if (wrapper) {
        wrapper.after(strengthContainer);
    } else {
        // Si no hay wrapper, insertar después del campo directamente
        passwordField.parentNode.insertBefore(strengthContainer, passwordField.nextSibling);
    }
    
    // Actualizar fortaleza cuando cambia la contraseña
    passwordField.addEventListener('input', function() {
        updatePasswordStrength(this.value, strengthFill, strengthText.querySelector('.fortaleza-value'));
    });
}

/**
 * Actualiza el indicador de fortaleza de contraseña
 */
function updatePasswordStrength(password, strengthFill, strengthText) {
    // Eliminar clases previas
    strengthFill.className = 'password-strength-value';
    
    // Si la contraseña está vacía
    if (!password) {
        strengthText.textContent = 'Vacío';
        return;
    }
    
    // Calcular fortaleza
    let strength = 0;
    let strengthClass = '';
    let strengthLabel = '';
    
    // Criterios de fortaleza
    if (password.length >= 8) strength += 1;
    if (/[A-Z]/.test(password)) strength += 1;
    if (/[0-9]/.test(password)) strength += 1;
    if (/[^a-zA-Z0-9]/.test(password)) strength += 1;
    
    // Determinar clase y texto
    switch (strength) {
        case 0:
        case 1:
            strengthClass = 'weak';
            strengthLabel = 'Débil';
            break;
        case 2:
            strengthClass = 'medium';
            strengthLabel = 'Media';
            break;
        case 3:
            strengthClass = 'good';
            strengthLabel = 'Buena';
            break;
        case 4:
            strengthClass = 'strong';
            strengthLabel = 'Fuerte';
            break;
    }
    
    // Aplicar clase y texto
    strengthFill.classList.add(strengthClass);
    strengthText.textContent = strengthLabel;
    
    // Establecer color del texto según la clase
    switch (strengthClass) {
        case 'weak':
            strengthText.style.color = '#e74c3c';
            break;
        case 'medium':
            strengthText.style.color = '#f39c12';
            break;
        case 'good':
            strengthText.style.color = '#2ecc71';
            break;
        case 'strong':
            strengthText.style.color = '#27ae60';
            break;
    }
}

/**
 * Configura la validación de coincidencia de contraseñas
 */
function setupPasswordMatch(password1, password2) {
    // Crear elemento para mensaje de error
    const errorMessage = document.createElement('div');
    errorMessage.className = 'password-match-error';
    errorMessage.style.color = '#e74c3c';
    errorMessage.style.fontSize = '13px';
    errorMessage.style.marginTop = '5px';
    errorMessage.style.display = 'none';
    errorMessage.textContent = 'Las contraseñas no coinciden';
    
    // Insertar después del segundo campo
    const wrapper = password2.closest('.password-field-container');
    if (wrapper) {
        wrapper.after(errorMessage);
    } else {
        password2.parentNode.insertBefore(errorMessage, password2.nextSibling);
    }
    
    // Función para validar coincidencia
    function validateMatch() {
        // Solo validar si ambos campos tienen valor
        if (password1.value && password2.value) {
            if (password1.value !== password2.value) {
                errorMessage.style.display = 'block';
            } else {
                errorMessage.style.display = 'none';
            }
        } else {
            errorMessage.style.display = 'none';
        }
    }
    
    // Validar cuando cambie cualquiera de los campos
    password1.addEventListener('input', validateMatch);
    password2.addEventListener('input', validateMatch);
}

/**
 * Reorganiza el formulario para mejor estructura
 */
function reorganizeForm() {
    // Buscar el formulario principal
    const form = document.querySelector('form[action*="/password/"]');
    if (!form) return;
    
    // Añadir clase para estilos específicos
    form.classList.add('password-change-form');
    
    // Buscar el título y mejorarlo
    const title = document.querySelector('h1');
    if (title) {
        title.innerHTML = title.innerHTML.replace('Cambiar contraseña:', '<strong>Cambiar contraseña:</strong>');
    }
    
    // Mejorar la sección de botones
    const submitRow = form.querySelector('.submit-row');
    if (!submitRow) {
        // Si no existe, crear uno
        const submitButton = form.querySelector('input[type="submit"]');
        if (submitButton) {
            const parent = submitButton.parentNode;
            const submitRow = document.createElement('div');
            submitRow.className = 'submit-row';
            parent.insertBefore(submitRow, submitButton);
            submitRow.appendChild(submitButton);
        }
    }
    
    // Mejorar campos existentes de fortaleza
    const existingStrength = document.querySelectorAll('.fortaleza');
    existingStrength.forEach(el => {
        // Si ya existe, mejorarlo
        if (!el.querySelector('.fortaleza-label')) {
            const textNode = el.firstChild;
            if (textNode && textNode.nodeType === Node.TEXT_NODE) {
                const label = document.createElement('span');
                label.className = 'fortaleza-label';
                label.textContent = textNode.textContent;
                el.replaceChild(label, textNode);
            }
        }
        
        // Mejorar el valor
        const valueNode = el.childNodes[1];
        if (valueNode && valueNode.nodeType === Node.TEXT_NODE) {
            const value = document.createElement('span');
            value.className = 'fortaleza-value';
            value.textContent = valueNode.textContent;
            el.replaceChild(value, valueNode);
        }
    });
    
    // Mejorar cualquier tabla presente
    const tables = form.querySelectorAll('table');
    tables.forEach(table => {
        // Buscar todos los td que contienen un campo
        const cells = table.querySelectorAll('td');
        cells.forEach(cell => {
            cell.style.padding = '10px';
        });
    });
}
