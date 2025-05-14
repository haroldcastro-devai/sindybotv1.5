/**
 * SBOT - JavaScript específico para la página de edición de usuario
 * URL: http://192.168.30.241:8000/admin/auth/user/3/change/
 * Implementado por Claude - Mayo 2025
 */

document.addEventListener('DOMContentLoaded', function() {
    // Solo ejecutar en la página de edición de usuario
    const isUserEdit = window.location.pathname.includes('/admin/auth/user/') && 
                       window.location.pathname.includes('/change/');
    
    if (!isUserEdit) return;
    
    console.log('Inicializando mejoras para la página de edición de usuario');
    
    // Añadir clase al body para identificar esta página
    document.body.classList.add('user-edit-page');
    
    // Mejorar el formulario principal
    const userForm = document.querySelector('form[id$="_form"]');
    if (userForm) {
        userForm.classList.add('user-edit-form');
        console.log('Formulario de usuario encontrado y mejorado');
    }
    
    // Identificar y mejorar campos específicos
    enhanceFormFields();
    
    // Mejorar la validación de formularios
    enhanceFormValidation();
    
    // Añadir ayuda contextual
    addContextualHelp();
    
    // Mejorar visualización de permisos
    enhancePermissionsDisplay();
    
    // Mejorar mensajes de error
    improveErrorMessages();
    
    // Añadir animaciones y transiciones
    addAnimations();
    
    console.log('Mejoras para la página de edición de usuario aplicadas correctamente');
});

/**
 * Mejora los campos del formulario con clases y atributos adicionales
 */
function enhanceFormFields() {
    // Mapeo de ID de campos con sus clases y placeholders
    const fieldMappings = [
        { id: 'id_username', classes: ['username-field', 'field-username'], placeholder: 'Nombre de usuario', icon: 'user' },
        { id: 'id_email', classes: ['email-field', 'field-email'], placeholder: 'correo@ejemplo.com', icon: 'mail' },
        { id: 'id_password1', classes: ['password-field', 'field-password'], placeholder: 'Contraseña segura', icon: 'lock' },
        { id: 'id_password2', classes: ['password-field', 'field-password'], placeholder: 'Confirmar contraseña', icon: 'lock' },
        { id: 'id_is_active', classes: ['active-field', 'field-is_active'], icon: 'check-circle' },
        { id: 'id_is_staff', classes: ['staff-field', 'field-is_staff'], icon: 'shield' },
        { id: 'id_is_superuser', classes: ['superuser-field', 'field-is_superuser'], icon: 'award' }
    ];
    
    // Aplicar mejoras a cada campo
    fieldMappings.forEach(mapping => {
        const field = document.getElementById(mapping.id);
        if (!field) return;
        
        // Añadir clases al campo
        mapping.classes.forEach(cls => field.classList.add(cls));
        
        // Añadir placeholder si corresponde
        if (mapping.placeholder) {
            field.setAttribute('placeholder', mapping.placeholder);
        }
        
        // Añadir ícono si corresponde
        if (mapping.icon && field.parentNode) {
            const row = field.closest('.form-row');
            if (row) {
                row.classList.add('has-icon', mapping.icon + '-icon');
                
                // Añadir clase al label si existe
                const label = row.querySelector('label');
                if (label) {
                    label.classList.add('with-icon');
                    label.setAttribute('data-icon', mapping.icon);
                }
            }
        }
        
        // Efectos de focus
        field.addEventListener('focus', function() {
            const row = this.closest('.form-row');
            if (row) row.classList.add('focused');
        });
        
        field.addEventListener('blur', function() {
            const row = this.closest('.form-row');
            if (row) row.classList.remove('focused');
        });
    });
    
    // Mejorar los checkboxes
    document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        const wrapper = document.createElement('div');
        wrapper.className = 'checkbox-wrapper';
        if (checkbox.parentNode) {
            checkbox.parentNode.insertBefore(wrapper, checkbox);
            wrapper.appendChild(checkbox);
            
            // Crear etiqueta visual para el checkbox
            const customCheckbox = document.createElement('span');
            customCheckbox.className = 'custom-checkbox';
            wrapper.appendChild(customCheckbox);
        }
    });
    
    console.log('Campos del formulario mejorados');
}

/**
 * Mejora la validación del formulario
 */
function enhanceFormValidation() {
    const form = document.querySelector('form.user-edit-form');
    if (!form) return;
    
    // Marcar campos requeridos
    const requiredFields = ['id_username'];
    requiredFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field && field.closest('.form-row')) {
            field.closest('.form-row').classList.add('required');
            
            // Añadir validación en tiempo real
            field.addEventListener('blur', function() {
                validateField(this);
            });
        }
    });
    
    // Validación de longitud de contraseña
    const passwordField = document.getElementById('id_password1');
    if (passwordField) {
        passwordField.addEventListener('input', function() {
            validatePasswordStrength(this);
        });
    }
    
    // Validar coincidencia de contraseñas
    const confirmPasswordField = document.getElementById('id_password2');
    if (confirmPasswordField && passwordField) {
        confirmPasswordField.addEventListener('input', function() {
            validatePasswordMatch(passwordField, this);
        });
    }
    
    console.log('Validación de formulario mejorada');
}

/**
 * Valida un campo individual
 */
function validateField(field) {
    const row = field.closest('.form-row');
    if (!row) return;
    
    // Eliminar mensajes de error previos
    const existingError = row.querySelector('.field-validation-error');
    if (existingError) existingError.remove();
    
    // Validar según el tipo de campo
    if (field.value.trim() === '' && row.classList.contains('required')) {
        showFieldError(field, 'Este campo es obligatorio');
        return false;
    }
    
    // Validación específica para email
    if (field.id === 'id_email' && field.value.trim() !== '') {
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailPattern.test(field.value)) {
            showFieldError(field, 'Por favor, ingresa un correo electrónico válido');
            return false;
        }
    }
    
    return true;
}

/**
 * Muestra un mensaje de error para un campo
 */
function showFieldError(field, message) {
    const row = field.closest('.form-row');
    if (!row) return;
    
    // Crear elemento de error
    const errorElement = document.createElement('div');
    errorElement.className = 'field-validation-error';
    errorElement.textContent = message;
    
    // Insertar después del campo
    const fieldContainer = field.parentNode;
    if (fieldContainer) {
        fieldContainer.appendChild(errorElement);
    }
    
    // Añadir clase de error al campo y fila
    field.classList.add('has-error');
    row.classList.add('has-error');
}

/**
 * Valida la fortaleza de la contraseña
 */
function validatePasswordStrength(passwordField) {
    const row = passwordField.closest('.form-row');
    if (!row) return;
    
    // Eliminar indicador de fortaleza previo
    const existingIndicator = row.querySelector('.password-strength');
    if (existingIndicator) existingIndicator.remove();
    
    // Si el campo está vacío, no mostrar indicador
    if (passwordField.value.trim() === '') return;
    
    // Crear indicador de fortaleza
    const strengthIndicator = document.createElement('div');
    strengthIndicator.className = 'password-strength';
    
    // Calcular fortaleza
    const password = passwordField.value;
    let strength = 0;
    let strengthClass = '';
    let strengthText = '';
    
    // Criterios de fortaleza
    if (password.length >= 8) strength += 1;
    if (password.match(/[A-Z]/)) strength += 1;
    if (password.match(/[0-9]/)) strength += 1;
    if (password.match(/[^a-zA-Z0-9]/)) strength += 1;
    
    // Determinar clase y texto
    switch (strength) {
        case 0:
        case 1:
            strengthClass = 'weak';
            strengthText = 'Débil';
            break;
        case 2:
            strengthClass = 'medium';
            strengthText = 'Media';
            break;
        case 3:
            strengthClass = 'good';
            strengthText = 'Buena';
            break;
        case 4:
            strengthClass = 'strong';
            strengthText = 'Fuerte';
            break;
    }
    
    // Configurar indicador
    strengthIndicator.classList.add(strengthClass);
    strengthIndicator.innerHTML = `
        <div class="strength-bar">
            <div class="strength-fill ${strengthClass}" style="width: ${strength * 25}%"></div>
        </div>
        <div class="strength-text">${strengthText}</div>
    `;
    
    // Añadir al formulario
    const fieldContainer = passwordField.parentNode;
    if (fieldContainer) {
        fieldContainer.appendChild(strengthIndicator);
    }
}

/**
 * Valida que las contraseñas coincidan
 */
function validatePasswordMatch(passwordField, confirmField) {
    const row = confirmField.closest('.form-row');
    if (!row) return;
    
    // Eliminar mensajes de error previos
    const existingError = row.querySelector('.field-validation-error');
    if (existingError) existingError.remove();
    
    // Si algún campo está vacío, no validar
    if (passwordField.value.trim() === '' || confirmField.value.trim() === '') return;
    
    // Validar coincidencia
    if (passwordField.value !== confirmField.value) {
        showFieldError(confirmField, 'Las contraseñas no coinciden');
        return false;
    }
    
    return true;
}

/**
 * Añade ayuda contextual para campos complejos
 */
function addContextualHelp() {
    // Mapeo de ID de campos con su texto de ayuda
    const helpMappings = [
        { selector: '.field-is_active', text: 'Los usuarios inactivos no pueden iniciar sesión.' },
        { selector: '.field-is_staff', text: 'Determina si el usuario puede acceder al sitio de administración.' },
        { selector: '.field-is_superuser', text: 'Otorga acceso completo a todas las funcionalidades sin restricciones.' },
        { selector: '.field-user_permissions', text: 'Asigna permisos específicos al usuario.' },
        { selector: '.field-groups', text: 'Los grupos ayudan a categorizar usuarios y asignar permisos comunes.' }
    ];
    
    // Aplicar ayuda a cada campo
    helpMappings.forEach(mapping => {
        const field = document.querySelector(mapping.selector);
        if (!field) return;
        
        // Verificar si ya tiene texto de ayuda
        const existingHelp = field.querySelector('.help');
        if (existingHelp) {
            existingHelp.textContent = mapping.text;
        } else {
            // Crear nuevo elemento de ayuda
            const helpElement = document.createElement('div');
            helpElement.className = 'help';
            helpElement.textContent = mapping.text;
            
            // Añadir después del campo
            field.appendChild(helpElement);
        }
    });
    
    console.log('Ayuda contextual añadida');
}

/**
 * Mejora la visualización de permisos de usuario
 */
function enhancePermissionsDisplay() {
    // Mejorar los selectores de permisos
    const selectors = document.querySelectorAll('.selector');
    selectors.forEach(selector => {
        // Añadir título para mayor claridad
        if (selector.closest('.field-user_permissions')) {
            const title = document.createElement('h3');
            title.className = 'selector-title';
            title.textContent = 'Asignar permisos al usuario';
            selector.parentNode.insertBefore(title, selector);
        } else if (selector.closest('.field-groups')) {
            const title = document.createElement('h3');
            title.className = 'selector-title';
            title.textContent = 'Asignar grupos al usuario';
            selector.parentNode.insertBefore(title, selector);
        }
        
        // Mejorar los botones de selección
        const chooserLinks = selector.querySelectorAll('.selector-chooser a');
        chooserLinks.forEach(link => {
            // Añadir títulos
            if (link.className.includes('selector-add')) {
                link.setAttribute('title', 'Añadir seleccionados');
            } else if (link.className.includes('selector-remove')) {
                link.setAttribute('title', 'Eliminar seleccionados');
            }
            
            // Añadir íconos más descriptivos
            if (link.textContent.includes('>')) {
                link.innerHTML = '<i class="feather icon-chevron-right"></i>';
            } else if (link.textContent.includes('<')) {
                link.innerHTML = '<i class="feather icon-chevron-left"></i>';
            }
        });
    });
    
    console.log('Visualización de permisos mejorada');
}

/**
 * Mejora los mensajes de error para mayor claridad
 */
function improveErrorMessages() {
    const errorLists = document.querySelectorAll('.errorlist');
    errorLists.forEach(list => {
        list.classList.add('improved-errors');
        
        // Añadir ícono de error
        const items = list.querySelectorAll('li');
        items.forEach(item => {
            item.innerHTML = '<i class="feather icon-alert-circle"></i> ' + item.textContent;
        });
    });
    
    console.log('Mensajes de error mejorados');
}

/**
 * Añade animaciones y transiciones para mejorar la experiencia
 */
function addAnimations() {
    // Animar aparición de fieldsets
    const fieldsets = document.querySelectorAll('fieldset.module');
    fieldsets.forEach((fieldset, index) => {
        fieldset.style.opacity = '0';
        fieldset.style.transform = 'translateY(20px)';
        fieldset.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        
        // Animar con retardo progresivo
        setTimeout(() => {
            fieldset.style.opacity = '1';
            fieldset.style.transform = 'translateY(0)';
        }, 100 * index);
    });
    
    // Animar aparición de botones
    const buttons = document.querySelectorAll('.submit-row input, .submit-row a');
    buttons.forEach((button, index) => {
        button.style.opacity = '0';
        button.style.transform = 'scale(0.95)';
        button.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        
        setTimeout(() => {
            button.style.opacity = '1';
            button.style.transform = 'scale(1)';
        }, 300 + (100 * index));
    });
    
    console.log('Animaciones añadidas');
}
