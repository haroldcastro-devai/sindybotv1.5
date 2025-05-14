/**
 * Scripts personalizados para el panel de administración
 */

document.addEventListener('DOMContentLoaded', function() {
    // Añadir efectos de hover a las filas de las tablas
    const tableRows = document.querySelectorAll('#changelist table tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('mouseover', function() {
            this.classList.add('hover');
        });
        row.addEventListener('mouseout', function() {
            this.classList.remove('hover');
        });
    });
    
    // Mejorar los checkboxes
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        // Crear un wrapper para estilizar mejor
        const wrapper = document.createElement('span');
        wrapper.className = 'custom-checkbox';
        checkbox.parentNode.insertBefore(wrapper, checkbox);
        wrapper.appendChild(checkbox);
        
        // Añadir efectos visuales
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                wrapper.classList.add('checked');
            } else {
                wrapper.classList.remove('checked');
            }
        });
        
        // Inicializar estado
        if (checkbox.checked) {
            wrapper.classList.add('checked');
        }
    });
    
    // Mejorar la visualización de los mensajes del sistema
    const messages = document.querySelectorAll('.messagelist li');
    if (messages.length > 0) {
        setTimeout(() => {
            messages.forEach(message => {
                message.style.opacity = '0';
                message.style.transition = 'opacity 0.5s ease';
            });
        }, 5000);
    }
    
    // Añadir indicadores visuales a los campos del formulario
    const formRows = document.querySelectorAll('.form-row');
    formRows.forEach(row => {
        const inputs = row.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('focus', function() {
                row.classList.add('focused');
            });
            input.addEventListener('blur', function() {
                row.classList.remove('focused');
            });
        });
    });
    
    // Animar la transición entre páginas
    const contentContainer = document.getElementById('content');
    if (contentContainer) {
        contentContainer.style.opacity = '0';
        contentContainer.style.transition = 'opacity 0.3s ease';
        setTimeout(() => {
            contentContainer.style.opacity = '1';
        }, 100);
    }
    
    // Mejora visual para el selector de fechas
    const dateInputs = document.querySelectorAll('.vDateField');
    dateInputs.forEach(input => {
        input.setAttribute('placeholder', 'YYYY-MM-DD');
        input.parentNode.classList.add('date-field');
    });
    
    // Añadir tooltips a los iconos de estado
    const stateIcons = document.querySelectorAll('.true, .false');
    stateIcons.forEach(icon => {
        icon.addEventListener('mouseover', function() {
            const title = this.getAttribute('title');
            if (title) {
                const tooltip = document.createElement('div');
                tooltip.className = 'status-tooltip';
                tooltip.textContent = title;
                document.body.appendChild(tooltip);
                
                const rect = this.getBoundingClientRect();
                tooltip.style.position = 'absolute';
                tooltip.style.top = (rect.bottom + window.pageYOffset + 5) + 'px';
                tooltip.style.left = (rect.left + window.pageXOffset + (rect.width/2) - (tooltip.offsetWidth/2)) + 'px';
                tooltip.style.backgroundColor = 'rgba(0,0,0,0.8)';
                tooltip.style.color = 'white';
                tooltip.style.padding = '5px 10px';
                tooltip.style.borderRadius = '4px';
                tooltip.style.fontSize = '12px';
                tooltip.style.zIndex = '1000';
                
                this._tooltip = tooltip;
            }
        });
        
        icon.addEventListener('mouseout', function() {
            if (this._tooltip) {
                document.body.removeChild(this._tooltip);
                this._tooltip = null;
            }
        });
    });
});

// Añadir una animación de carga para las acciones de guardado
window.onload = function() {
    const saveButtons = document.querySelectorAll('input[type="submit"], .submit-row input');
    saveButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Solo para botones que no son "Eliminar"
            if (!this.classList.contains('deletelink')) {
                const originalText = this.value;
                this.setAttribute('data-original-text', originalText);
                this.value = 'Procesando...';
                this.style.opacity = '0.7';
                this.style.cursor = 'wait';
                
                // Revertir si tarda demasiado
                setTimeout(() => {
                    if (this.value === 'Procesando...') {
                        this.value = originalText;
                        this.style.opacity = '1';
                        this.style.cursor = 'pointer';
                    }
                }, 10000);
            }
        });
    });
};
