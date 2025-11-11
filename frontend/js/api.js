/**
 * API Client для Service Desk
 */

const API_BASE = 'http://127.0.0.1:8001';

class ApiClient {
    constructor() {
        this.token = localStorage.getItem('token');
    }

    getHeaders(includeAuth = true) {
        const headers = {
            'Content-Type': 'application/json',
        };
        if (includeAuth && this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        return headers;
    }

    async request(endpoint, options = {}) {
        const url = `${API_BASE}${endpoint}`;
        const config = {
            ...options,
            headers: this.getHeaders(options.auth !== false),
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Request failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Auth
    async login(email, password) {
        const data = await this.request('/auth/login/json', {
            method: 'POST',
            auth: false,
            body: JSON.stringify({ email, password }),
        });
        this.token = data.access_token;
        localStorage.setItem('token', this.token);
        return data;
    }

    async getMe() {
        return this.request('/auth/me');
    }

    logout() {
        this.token = null;
        localStorage.removeItem('token');
        localStorage.removeItem('user');
    }

    // Tickets (placeholder - буде розширено пізніше)
    async getTickets(filters = {}) {
        const params = new URLSearchParams(filters);
        return this.request(`/tickets?${params}`);
    }

    async getTicket(id) {
        return this.request(`/tickets/${id}`);
    }

    async createTicket(data) {
        return this.request('/tickets', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    isAuthenticated() {
        return !!this.token;
    }
}

const api = new ApiClient();
