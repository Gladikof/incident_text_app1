/**
 * API Client для Service Desk
 */

const API_BASE = 'http://127.0.0.1:8003';

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

    // Tickets
    async getTickets(filters = {}) {
        const params = new URLSearchParams();
        Object.keys(filters).forEach(key => {
            if (filters[key] !== null && filters[key] !== undefined) {
                params.append(key, filters[key]);
            }
        });
        const queryString = params.toString();
        return this.request(`/tickets${queryString ? '?' + queryString : ''}`);
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

    async updateTicket(id, data) {
        return this.request(`/tickets/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    }

    async updateTicketStatus(id, status) {
        return this.request(`/tickets/${id}/status`, {
            method: 'PATCH',
            body: JSON.stringify({ status }),
        });
    }

    async claimTicket(id) {
        return this.request(`/tickets/${id}/claim`, {
            method: 'POST',
            body: JSON.stringify({}),
        });
    }

    async assignTicket(id, assigneeId) {
        return this.request(`/tickets/${id}/assign`, {
            method: 'PATCH',
            body: JSON.stringify({ assignee_id: assigneeId }),
        });
    }

    async resolveTriage(id, priorityFinal, categoryFinal) {
        return this.request(`/tickets/${id}/triage/resolve`, {
            method: 'PATCH',
            body: JSON.stringify({
                priority_final: priorityFinal,
                category_final: categoryFinal
            }),
        });
    }

    // Departments
    async getDepartments() {
        return this.request('/departments');
    }

    isAuthenticated() {
        return !!this.token;
    }
}

const api = new ApiClient();
