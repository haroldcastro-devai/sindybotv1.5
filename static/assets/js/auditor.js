// Función para ejecutar el script
function ejecutarScript() {
    fetch('/abrir_ubicacion/')
        .then(response => {
            if (response.ok) {
                console.log('Script ejecutado correctamente');
            } else {
                console.error('Error al ejecutar el script');
            }
        })
        .catch(error => console.error('Error al ejecutar el script:', error));
}

// Función para mostrar el modal
function mostrarModal() {
    var modal = document.getElementById('myModal');
    modal.style.display = "block";
}

// Función para cerrar el modal
function cerrarModal() {
    var modal = document.getElementById('myModal');
    modal.style.display = "none";
}

// Función para seleccionar el tipo de auditoría
function seleccionarAuditoria(tipo) {
    if (tipo === 'directa') {
        mostrarModal();
    } else {
        alert('Ha seleccionado la auditoría ' + tipo.toUpperCase() + '.');
        // Aquí agregar más lógica según sea necesario, como enviar la opción seleccionada al servidor, etc.
    }
}

// Función para mostrar las fechas seleccionadas
function mostrarFechas() {
    // Obtener las fechas seleccionadas
    var startDate = document.getElementById('start_date').value;
    var endDate = document.getElementById('end_date').value;

    // Mostrar las fechas en una ventana emergente
    alert('Fechas seleccionadas:\nDía de inicio: ' + startDate + '\nDía final: ' + endDate);
}

// Función para actualizar la tabla
function actualizarTabla() {
    $.ajax({
        url: '/config/',
        dataType: 'json',
        success: function(data) {
            // Limpia la tabla
            $('#tablaActividad tbody').empty();
            // Agrega las nuevas filas
            $.each(data, function(index, registro) {
                var fila = '<tr>' + 
                    '<td>' + registro.reg_activ_fecha + '</td>' +
                    '<td>' + registro.reg_activ_user + '</td>' + 
                    '<td>' + registro.reg_activ_archproc + '</td>' + 
                    '<td>' + registro.reg_sum_ventpos + '</td>' + 
                    '<td>' + registro.reg_sum_ventneg + '</td>' + 
                    '<td>' + registro.reg_tip_consulta + '</td>' + 
                    '</tr>';
                $('#tablaActividad tbody').append(fila);
            });
        }
    });
}

// Función para verificar la señal del toast
function verificarSenalToast() {
    $.ajax({
        url: '',  // URL apropiada
        success: function(data) {
            if (data.senal == 'mostrar_toast') {
                // Mostrar el toast
                var toastEl = $('#toastDirectorio');
                var toast = new bootstrap.Toast(toastEl);
                toast.show();
                // Eliminar el archivo de señal
                $.ajax({
                    url: '',  //  URL apropiada
                });
            }
        }
    });
}

// Verificar la señal periódicamente
setInterval(verificarSenalToast, 1000); // Verifica cada 1 segundo

// Ejecutar cuando el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', function() {
    // Aquí puedes agregar cualquier inicialización adicional que necesites
});