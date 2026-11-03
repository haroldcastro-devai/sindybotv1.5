// Configuración de la API (autenticación por sesión Django + CSRF)
const BASE_URL = window.location.origin;

function getCsrfToken() {
    const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
}

const API_CONFIG = {
    getHeaders: (jsonBody = true) => {
        const headers = {
            Accept: 'application/json',
            'X-CSRFToken': getCsrfToken(),
        };
        if (jsonBody) {
            headers['Content-Type'] = 'application/json';
        }
        return headers;
    },

    apiRequest: async (endpoint, options = {}) => {
        const method = (options.method || 'GET').toUpperCase();
        const jsonBody = method !== 'GET' && !(options.body instanceof Blob);
        const response = await fetch(`${BASE_URL}${endpoint}`, {
            credentials: 'include',
            ...options,
            headers: {
                ...API_CONFIG.getHeaders(jsonBody),
                ...(options.headers || {}),
            },
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return response.json();
    },

    downloadPost: async (endpoint) => {
        const response = await fetch(`${BASE_URL}${endpoint}`, {
            method: 'POST',
            credentials: 'include',
            headers: API_CONFIG.getHeaders(false),
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.blob();
    },
};

const DashboardAPI = {
    // Login vía formulario Django: /accounts/auth-signin/
    loginViaSession: () => {
        window.location.href = '/accounts/auth-signin/';
    },

    getStats: () => API_CONFIG.apiRequest('/api/dashboard/stats/'),

    getGraphData: () => API_CONFIG.apiRequest('/api/dashboard/graph-data/'),

    getActivityLog: () => API_CONFIG.apiRequest('/api/activity-log/'),

    generateReport: () => API_CONFIG.downloadPost('/api/generate-report/'),
};

export { API_CONFIG, DashboardAPI };
