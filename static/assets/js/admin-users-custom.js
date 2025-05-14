/**
 * Script para mejorar la visualización de la página de administración de usuarios
 * URL: http://192.168.30.241:8000/admin/auth/user/
 */

document.addEventListener('DOMContentLoaded', function() {
    // Solo ejecutar en la página de administración de usuarios
    if (window.location.pathname.indexOf('/admin/auth/user/') === 0) {
        
        // Traducciones específicas
        const translations = {
            'Add user': 'Añadir usuario',
            'User': 'Usuario',
            'Users': 'Usuarios',
            'Staff status': 'Es staff',
            'Superuser status': 'Es superusuario',
            'Active': 'Activo',
            'Filter': 'Filtrar',
            'By staff status': 'Por estado de staff',
            'By superuser status': 'Por estado de superusuario',
            'By active': 'Por activo',
            'Username': 'Nombre de usuario',
            'Email address': 'Correo electrónico',
            'First name': 'Nombre',
            'Last name': 'Apellido',
            'Password': 'Contraseña',
            'Save': 'Guardar',
            'Save and continue editing': 'Guardar y continuar editando',
            'Save and add another': 'Guardar y añadir otro',
            'Yes': 'Sí',
            'No': 'No',
            'Unknown': 'Desconocido',
            'All': 'Todos'
        };
        
        // Función para traducir textos en la página
        function translateText() {
            // Traducir textos en los elementos
            document.querySelectorAll('*').forEach(function(el) {
                if (el.childNodes && el.childNodes.length === 1 && el.childNodes[0].nodeType === 3) {
                    const text = el.innerText.trim();
                    if (translations[text]) {
                        el.innerText = translations[text];
                    }
                }
            });
            
            // Traducir atributos title y placeholder
            document.querySelectorAll('[title], [placeholder]').forEach(function(el) {
                if (el.hasAttribute('title') && translations[el.getAttribute('title')]) {
                    el.setAttribute('title', translations[el.getAttribute('title')]);
                }
                if (el.hasAttribute('placeholder') && translations[el.getAttribute('placeholder')]) {
                    el.setAttribute('placeholder', translations[el.getAttribute('placeholder')]);
                }
            });
            
            // Traducir enlaces
            document.querySelectorAll('a').forEach(function(el) {
                if (el.innerText && translations[el.innerText.trim()]) {
                    el.innerText = translations[el.innerText.trim()];
                }
            });
            
            // Traducir botones
            document.querySelectorAll('button, input[type="submit"], input[type="button"]').forEach(function(el) {
                if (el.value && translations[el.value]) {
                    el.value = translations[el.value];
                }
                if (el.innerText && translations[el.innerText.trim()]) {
                    el.innerText = translations[el.innerText.trim()];
                }
            });
        }
        
        // Mejorar la apariencia de los checkboxes
        function enhanceCheckboxes() {
            document.querySelectorAll('input[type="checkbox"]').forEach(function(checkbox) {
                // Asegurarse de que los checkboxes tengan el estilo correcto
                checkbox.classList.add('custom-checkbox');
                
                // Para checkboxes en cabeceras de tabla (seleccionar todos)
                if (checkbox.id === 'action-toggle') {
                    checkbox.setAttribute('title', 'Seleccionar todos');
                }
            });
        }
        
        // Función para mejorar la usabilidad y apariencia
        function enhanceUI() {
            // Añadir clases a la tabla para mejorar estilos
            const resultsTable = document.querySelector('#result_list');
            if (resultsTable) {
                resultsTable.classList.add('admin-user-table');
                
                // Mejorar encabezados de tabla
                const headers = resultsTable.querySelectorAll('thead th');
                headers.forEach(function(header) {
                    if (header.classList.contains('action-checkbox-column')) {
                        const label = header.querySelector('label');
                        if (label) label.textContent = '';
                    }
                });
                
                // Añadir tooltips a las acciones
                const actionLinks = document.querySelectorAll('.field-username a');
                actionLinks.forEach(function(link) {
                    if (link.textContent) {
                        link.setAttribute('title', 'Editar usuario: ' + link.textContent);
                    }
                });
            }
            
            // Añadir ícono a botón de añadir usuario
            const addButton = document.querySelector('.addlink');
            if (addButton) {
                addButton.innerHTML = '<span class="btn-icon">+</span> ' + addButton.innerHTML;
                addButton.classList.add('btn', 'btn-sm', 'btn-success');
            }
            
            // Mejorar la visualización de botones de acción
            const actionButtons = document.querySelectorAll('.actions button');
            actionButtons.forEach(function(button) {
                button.classList.add('btn', 'btn-sm', 'btn-primary');
            });
            
            // Mejorar paginación
            const paginator = document.querySelector('.paginator');
            if (paginator) {
                paginator.classList.add('admin-paginator');
            }
        }
        
        // Ejecutar funciones de mejora
        translateText();
        enhanceCheckboxes();
        enhanceUI();
        
        // Re-aplicar después de cargar completamente la página
        window.addEventListener('load', function() {
            setTimeout(function() {
                translateText();
                enhanceCheckboxes();
                enhanceUI();
            }, 100);
        });
    }
});
