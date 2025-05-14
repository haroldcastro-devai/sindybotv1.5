// Configuración de la API
const BASE_URL = 'http://192.168.30.241:8000'; // URL base del servidor

const API_CONFIG = {
    getHeaders: () => {
        const token = localStorage.getItem('access_token');
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : '',
        };
    },
    
    apiRequest: async (endpoint, options = {}) => {
        const headers = API_CONFIG.getHeaders();
        const defaultOptions = {
            headers,
            credentials: 'include',
        };

        const response = await fetch(`${BASE_URL}${endpoint}`, {
            ...defaultOptions,
            ...options,
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }
};

// Endpoints del dashboard
const DashboardAPI = {
    // Autenticación
    login: (credentials) => {
        return API_CONFIG.apiRequest('/api/auth/login/', {
            method: 'POST',
            body: JSON.stringify(credentials)
        });
    },

    // Estadísticas del dashboard
    getStats: () => {
        return API_CONFIG.apiRequest('/api/dashboard/stats/');
    },

    // Datos para las gráficas
    getGraphData: () => {
        return API_CONFIG.apiRequest('/api/dashboard/graph-data/');
    },

    // Log de actividades
    getActivityLog: () => {
        return API_CONFIG.apiRequest('/api/activity-log/');
    },

    // Generar reporte
    generateReport: () => {
        return API_CONFIG.apiRequest('/api/generate-report/', {
            method: 'POST'
        });
    }
};

export { API_CONFIG, DashboardAPI };