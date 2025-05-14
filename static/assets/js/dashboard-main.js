import { DashboardAPI } from './api/config.js';

// Función para cargar los datos del dashboard
async function loadDashboardData() {
    try {
        // Obtener estadísticas
        const stats = await DashboardAPI.getStats();
        updateDashboardStats(stats);

        // Obtener datos para gráficas
        const response = await fetch('/obtener_datos_grafica/');
        const graphData = await response.json();
        updateDashboardGraphs(graphData);

        // Obtener log de actividades
        const activityLog = await DashboardAPI.getActivityLog();
        updateActivityLog(activityLog);
    } catch (error) {
        console.error('Error cargando datos del dashboard:', error);
    }
}

// Función para actualizar las estadísticas en el dashboard
function updateDashboardStats(stats) {
    document.getElementById('total-records').textContent = stats.total_records;
    document.getElementById('ventas-positivas').textContent = stats.ventas_positivas;
    document.getElementById('ventas-negativas').textContent = stats.ventas_negativas;
    document.getElementById('porcentaje-positivas').textContent = `${stats.porcentaje_positivas}%`;
}

// Función para actualizar las gráficas
function updateDashboardGraphs(data) {
    const chartElement = document.querySelector("#chartdiv");
    if (!chartElement) {
        console.error('Elemento de gráfica no encontrado');
        return;
    }

    const options = {
        series: [{
            name: 'Ventas Totales',
            data: data.map(item => item.sales1)
        }, {
            name: 'Ventas Positivas',
            data: data.map(item => item.sales0)
        }, {
            name: 'Ventas Negativas',
            data: data.map(item => item.market1)
        }],
        chart: {
            height: 350,
            type: 'line',
            toolbar: {
                show: true
            },
        },
        colors: ['#008FFB', '#00E396', '#FF4560'],
        dataLabels: {
            enabled: true,
        },
        stroke: {
            curve: 'smooth'
        },
        grid: {
            borderColor: '#e7e7e7',
            row: {
                colors: ['#f3f3f3', 'transparent'],
                opacity: 0.5
            },
        },
        markers: {
            size: 1
        },
        xaxis: {
            categories: data.map(item => item.date),
            title: {
                text: 'Fecha'
            }
        },
        yaxis: {
            title: {
                text: 'Cantidad'
            }
        },
        legend: {
            position: 'top',
            horizontalAlign: 'right',
            floating: true,
            offsetY: -25,
            offsetX: -5
        }
    };

    // Destruir la instancia anterior si existe
    if (window.myChart) {
        window.myChart.destroy();
    }

    // Crear nueva instancia de ApexCharts
    window.myChart = new ApexCharts(chartElement, options);
    window.myChart.render();
}

// Función para actualizar el log de actividades
function updateActivityLog(activities) {
    const logContainer = document.getElementById('activity-log');
    if (logContainer) {
        logContainer.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <div class="activity-timestamp">${activity.fecha}</div>
                <div class="activity-type">${activity.tipo_consulta}</div>
                <div class="activity-directory">${activity.directorio}</div>
            </div>
        `).join('');
    }
}

// Iniciar la carga de datos cuando el documento esté listo
document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
    
    // Actualizar datos cada 5 minutos
    setInterval(loadDashboardData, 300000);
});

// Función para descargar reporte
document.getElementById('download-report-btn')?.addEventListener('click', async () => {
    try {
        const response = await DashboardAPI.generateReport();
        // Manejar la descarga del archivo
    } catch (error) {
        console.error('Error generando reporte:', error);
    }
});