document.addEventListener('DOMContentLoaded', function() {
    // Variable global para guardar el intervalo del seguimiento
    let intervaloSeguimiento = null;
    let procesoAuditoriaEnEjecucion = false;
    
    // Verificar si hay un proceso de auditoría en curso al cargar la página
    if (sessionStorage.getItem('auditoria_en_progreso') === 'true') {
        // Remover estilos inline que puedan estar causando problemas
        var modalElement = document.getElementById('modalProgreso');
        modalElement.removeAttribute('style');
        
        // Asegurar que el modal tenga las clases correctas
        modalElement.classList.add('fade', 'show');
        
        // Mostrar modal de progreso automáticamente
        var modalProgreso = new bootstrap.Modal(document.getElementById('modalProgreso'), {
            backdrop: 'static',
            keyboard: false
        });
        modalProgreso.show();
        
        // Agregar evento para prevenir que el modal se cierre
        document.getElementById('modalProgreso').addEventListener('hide.bs.modal', function (event) {
            // Si el proceso aún está en curso, prevenir que se cierre el modal
            if (sessionStorage.getItem('auditoria_en_progreso') === 'true') {
                event.preventDefault();
            }
        });
        
        // Cargar el último estado conocido del progreso
        const ultimoProgreso = JSON.parse(sessionStorage.getItem('progreso_auditoria') || '{}');
        if (Object.keys(ultimoProgreso).length > 0) {
            actualizarModalProgreso(ultimoProgreso);
        }
        
        // Iniciar verificación de progreso
        iniciarSeguimientoProgreso();
    }
    
    // Botón para abrir el modal
    document.getElementById('btnAbrirModal').addEventListener('click', function() {
        var modalAuditoria = new bootstrap.Modal(document.getElementById('modalAuditoria'));
        modalAuditoria.show();
    });
    
    // Botón para iniciar la auditoría
    document.getElementById('btnIniciarAuditoria').addEventListener('click', function() {
        const fileInput = document.getElementById('archivo_excel');
        if (!fileInput.files.length) {
            alert('Por favor, seleccione un archivo Excel');
            return;
        }
        
        // Mostrar spinner
        document.getElementById('formAuditoriaRemota').classList.add('d-none');
        document.getElementById('processingInfo').classList.remove('d-none');
        document.getElementById('btnIniciarAuditoria').disabled = true;
        
        // Crear FormData y añadir el archivo
        const formData = new FormData();
        formData.append('archivo_excel', fileInput.files[0]);
        
        // Enviar petición AJAX
        fetch('/iniciar_auditoria_remota/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            // Cerrar modal inicial
            var modalAuditoria = bootstrap.Modal.getInstance(document.getElementById('modalAuditoria'));
            modalAuditoria.hide();
            
            if (data.success) {
                // Mostrar modal de progreso
                var modalProgreso = new bootstrap.Modal(document.getElementById('modalProgreso'), {
                    backdrop: 'static',
                    keyboard: false
                });
                
                // Remover estilos inline que puedan estar causando problemas
                var modalElement = document.getElementById('modalProgreso');
                modalElement.removeAttribute('style');
                
                // Asegurar que el modal tenga las clases correctas
                modalElement.classList.add('fade', 'show');
                
                // Agregar evento para prevenir que el modal se cierre
                document.getElementById('modalProgreso').addEventListener('hide.bs.modal', function (event) {
                    // Si el proceso aún está en curso, prevenir que se cierre el modal
                    if (sessionStorage.getItem('auditoria_en_progreso') === 'true') {
                        event.preventDefault();
                    }
                });
                
                modalProgreso.show();
                
                // Iniciar verificación de progreso
                iniciarSeguimientoProgreso();
            } else {
                // Mostrar toast con error
                const toast = document.getElementById('toastResultado');
                const toastMessage = document.getElementById('toastMessage');
                
                toast.classList.remove('text-bg-success');
                toast.classList.add('text-bg-danger');
                toastMessage.textContent = data.error || 'Error al procesar la solicitud';
                
                const bsToast = new bootstrap.Toast(toast);
                bsToast.show();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al procesar la solicitud: ' + error);
        })
        .finally(() => {
            // Restaurar formulario
            document.getElementById('formAuditoriaRemota').classList.remove('d-none');
            document.getElementById('processingInfo').classList.add('d-none');
            document.getElementById('btnIniciarAuditoria').disabled = false;
            fileInput.value = '';
        });
    });
    
    // Función para obtener el token CSRF
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
    
    // Función para iniciar el seguimiento del progreso
    // Evento para el botón de cancelar auditoria
    document.getElementById('btnCancelarAuditoria').addEventListener('click', function() {
        // Mostrar modal de confirmación
        var modalConfirmacion = new bootstrap.Modal(document.getElementById('modalConfirmacionCancelar'));
        modalConfirmacion.show();
    });
    
    // Evento para confirmar cancelación
    document.getElementById('btnConfirmarCancelar').addEventListener('click', function() {
        // Ocultar modal de confirmación
        var modalConfirmacion = bootstrap.Modal.getInstance(document.getElementById('modalConfirmacionCancelar'));
        modalConfirmacion.hide();
        
        // Mostrar spinner o indicador de cancelación
        document.getElementById('btnCancelarAuditoria').disabled = true;
        document.getElementById('btnCancelarAuditoria').innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Cancelando...';
        
        // Enviar petición para cancelar el proceso
        fetch('/cancelar_auditoria/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Limpiar sessionStorage
                sessionStorage.removeItem('auditoria_en_progreso');
                sessionStorage.removeItem('progreso_auditoria');
                
                // Detener el intervalo de verificación
                if (intervaloSeguimiento) {
                    clearInterval(intervaloSeguimiento);
                    intervaloSeguimiento = null;
                }
                
                // Actualizar el modal de progreso
                document.getElementById('currentFile').textContent = 'Proceso cancelado';
                document.getElementById('progressBar').style.width = '100%';
                document.getElementById('progressBar').textContent = 'Cancelado';
                document.getElementById('progressBar').classList.remove('progress-bar-animated');
                document.getElementById('progressBar').classList.remove('bg-primary');
                document.getElementById('progressBar').classList.add('bg-danger');
                
                // Añadir mensaje al log de actividad
                const activityLog = document.getElementById('activityLog');
                const hora = new Date().toTimeString().split(' ')[0];
                const actividadElement = document.createElement('div');
                actividadElement.innerHTML = `<small><strong>${hora}</strong>: <span class="text-danger">Proceso cancelado por el usuario</span></small>`;
                activityLog.appendChild(actividadElement);
                activityLog.scrollTop = activityLog.scrollHeight;
                
                // Esperar un poco y cerrar el modal
                setTimeout(function() {
                    var modalProgreso = bootstrap.Modal.getInstance(document.getElementById('modalProgreso'));
                    if (modalProgreso) {
                        modalProgreso.hide();
                    }
                    
                    // Mostrar modal de resultado cancelado
                    document.getElementById('totalArchivosCancelados').textContent = data.archivos_procesados || 0;
                    var modalCancelado = new bootstrap.Modal(document.getElementById('modalResultadoCancelado'));
                    modalCancelado.show();
                    
                    // Actualizar la tabla
                    actualizarTabla();
                }, 2000);
            } else {
                // Restaurar botón en caso de error
                document.getElementById('btnCancelarAuditoria').disabled = false;
                document.getElementById('btnCancelarAuditoria').textContent = 'Cancelar proceso';
                
                // Mostrar mensaje de error
                alert('Error al cancelar el proceso: ' + (data.error || 'Error desconocido'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            // Restaurar botón
            document.getElementById('btnCancelarAuditoria').disabled = false;
            document.getElementById('btnCancelarAuditoria').textContent = 'Cancelar proceso';
            alert('Error al procesar la solicitud de cancelación: ' + error);
        });
    });
    
    function iniciarSeguimientoProgreso() {
        // Guardar en sessionStorage que hay un proceso en curso
        sessionStorage.setItem('auditoria_en_progreso', 'true');
        procesoAuditoriaEnEjecucion = true;
        let contador = 0;
        let falloConsecutivo = 0;
        
        // Almacenar el intervalo en la variable global para poder cancelarlo
        intervaloSeguimiento = setInterval(function() {
            fetch('/ver_progreso_auditoria/')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Error en la respuesta del servidor');
                }
                return response.json();
            })
            .then(data => {
                // Reiniciar contador de fallos
                falloConsecutivo = 0;
                contador++;
                
                // Actualizar el modal y guardar progreso
                actualizarModalProgreso(data);
                sessionStorage.setItem('progreso_auditoria', JSON.stringify(data));
                
                // Verificar si el proceso sigue activo al menos cada 10 verificaciones
                // Esto evita que el modal se quede abierto si hay un error en el servidor
                if (contador >= 10) {
                    contador = 0;
                    verificarProcesoActivo();
                }
                
                // Si el proceso ha finalizado con éxito, limpiar todo
                if (!data.en_progreso) {
                    clearInterval(intervaloSeguimiento);
                    intervaloSeguimiento = null;
                    procesoAuditoriaEnEjecucion = false;
                    sessionStorage.removeItem('auditoria_en_progreso');
                    sessionStorage.removeItem('progreso_auditoria');
                    
                    // Esperar un poco y cerrar el modal solo cuando el proceso ha finalizado
                    setTimeout(function() {
                        var modalProgreso = bootstrap.Modal.getInstance(document.getElementById('modalProgreso'));
                        if (modalProgreso) {
                            modalProgreso.hide();
                        }
                        
                        // Mostrar modal de finalización en lugar del toast
                        document.getElementById('totalArchivosFinalizados').textContent = data.archivos_procesados;
                        var modalResultado = new bootstrap.Modal(document.getElementById('modalResultadoFinal'));
                        modalResultado.show();
                        
                        // Actualizar la tabla
                        actualizarTabla();
                    }, 2000);
                }
            })
            .catch(error => {
                console.error('Error al verificar progreso:', error);
                falloConsecutivo++;
                
                // Si hay 5 fallos consecutivos, verificar si el proceso sigue activo
                if (falloConsecutivo >= 5) {
                    verificarProcesoActivo();
                }
            });
        }, 2000); // Verificar cada 2 segundos
        
        // Función para verificar si el proceso sigue activo
        function verificarProcesoActivo() {
            fetch('/ver_progreso_auditoria/', { 
                method: 'GET',
                headers: { 'Cache-Control': 'no-cache' } 
            })
            .then(response => response.json())
            .then(data => {
                // Si el proceso no está activo, limpiar todo
                if (!data.en_progreso) {
                    clearInterval(intervalo);
                    sessionStorage.removeItem('auditoria_en_progreso');
                    sessionStorage.removeItem('progreso_auditoria');
                }
            })
            .catch(() => {
                // En caso de error, mantener el intervalo activo
                console.log('Error al verificar si el proceso sigue activo');
            });
        }
    }
    
    // Función para actualizar el modal de progreso
    function actualizarModalProgreso(data) {
        // Actualizar barra de progreso
        const progressBar = document.getElementById('progressBar');
        progressBar.style.width = `${data.porcentaje}%`;
        progressBar.textContent = `${data.porcentaje}%`;
        progressBar.setAttribute('aria-valuenow', data.porcentaje);
        
        // Actualizar archivo actual
        if (data.archivo_actual) {
            document.getElementById('currentFile').textContent = data.archivo_actual;
        }
        
        // Actualizar fecha actual
        if (data.fecha_actual) {
            document.getElementById('currentDate').textContent = data.fecha_actual;
        }
        
        // Actualizar contadores
        document.getElementById('filesProcessed').textContent = data.archivos_procesados;
        document.getElementById('filesRemaining').textContent = data.pendientes;
        document.getElementById('timeElapsed').textContent = data.tiempo_transcurrido;
        
        // Actualizar actividad
        const activityLog = document.getElementById('activityLog');
        activityLog.innerHTML = '';
        
        if (data.actividad && data.actividad.length > 0) {
            data.actividad.forEach(actividad => {
                const actividadElement = document.createElement('div');
                actividadElement.innerHTML = `<small><strong>${actividad.hora}</strong>: ${actividad.mensaje}</small>`;
                activityLog.appendChild(actividadElement);
            });
            
            // Hacer scroll al final del log
            activityLog.scrollTop = activityLog.scrollHeight;
        }
    }
    
    // Verificar si hay un resultado pendiente
    function verificarResultadoPendiente() {
        fetch('/ver_senal_toast/')
        .then(response => response.json())
        .then(data => {
            if (data.mostrar) {
                const toast = document.getElementById('toastResultado');
                const toastMessage = document.getElementById('toastMessage');
                
                if (data.tipo === 'success') {
                    toast.classList.remove('text-bg-danger');
                    toast.classList.add('text-bg-success');
                    toastMessage.textContent = 'Proceso completado con éxito. ' + 
                        'Se procesaron ' + data.total_archivos + ' archivos.';
                } else {
                    toast.classList.remove('text-bg-success');
                    toast.classList.add('text-bg-danger');
                    toastMessage.textContent = 'Error: ' + data.mensaje;
                }
                
                const bsToast = new bootstrap.Toast(toast);
                bsToast.show();
                
                // Actualizar la tabla
                actualizarTabla();
            }
        })
        .catch(error => console.error('Error:', error));
    }
    
    // Verificar periódicamente
    setInterval(verificarResultadoPendiente, 3000);
});