import { DashboardAPI } from './api/config.js';

// Función para cargar los datos del dashboard
async function loadDashboardData() {
    try {
        // Obtener estadísticas
        const stats = await DashboardAPI.getStats();
        updateDashboardStats(stats);

        // Obtener datos para gráficas
        const graphData = await DashboardAPI.getGraphData();
        updateDashboardGraphs(graphData);

        // Obtener log de actividades
        const activityLog = await DashboardAPI.getActivityLog();
        updateActivityLog(activityLog);
    } catch (error) {
        console.error('Error cargando datos del dashboard:', error);
        // Manejar el error apropiadamente
    }
}

// Función para actualizar las estadísticas en el dashboard
function updateDashboardStats(stats) {
    // Actualizar los elementos del DOM con las estadísticas
    document.getElementById('total-records').textContent = stats.total_records;
    document.getElementById('ventas-positivas').textContent = stats.ventas_positivas;
    document.getElementById('ventas-negativas').textContent = stats.ventas_negativas;
    document.getElementById('porcentaje-positivas').textContent = `${stats.porcentaje_positivas}%`;
}

// Función para actualizar las gráficas
function updateDashboardGraphs(data) {
    // Aquí va tu código para actualizar las gráficas
    // Por ejemplo, si usas una librería de gráficas como Chart.js
    if (window.myChart) {
        window.myChart.data.datasets = [
            {
                label: 'Ventas Totales',
                data: data.map(item => item.total_ventas),
                // ... más configuración de la gráfica
            },
            // ... más datasets
        ];
        window.myChart.update();
    }
}

// Función para actualizar el log de actividades
function updateActivityLog(activities) {
    const logContainer = document.getElementById('activity-log');
    logContainer.innerHTML = activities.map(activity => `
        <div class="activity-item">
            <div class="activity-timestamp">${activity.fecha}</div>
            <div class="activity-type">${activity.tipo_consulta}</div>
            <div class="activity-directory">${activity.directorio}</div>
        </div>
    `).join('');
}

// Iniciar la carga de datos cuando el documento esté listo
document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
    
    // Actualizar datos cada cierto tiempo si es necesario
    setInterval(loadDashboardData, 300000); // Actualizar cada 5 minutos
});

// Función para descargar reporte
document.getElementById('download-report-btn')?.addEventListener('click', async () => {
    try {
        const response = await DashboardAPI.generateReport();
        // Manejar la descarga del archivo
        // ... código para descargar el archivo
    } catch (error) {
        console.error('Error generando reporte:', error);
        // Manejar el error
    }
});