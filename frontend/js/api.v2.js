/**
 * API Client для Service Desk
 */

const isHttpOrigin = typeof window !== 'undefined'
    && window.location
    && window.location.origin
    && window.location.origin.startsWith('http');

// Use current origin when served over HTTP(S); fallback to localhost for offline previews.
const API_BASE = isHttpOrigin ? window.location.origin : 'http://127.0.0.1:8000';

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

    async resolveTriage(id, priorityFinal, categoryFinal, reason = null) {
        const payload = {
            priority_final: priorityFinal,
            category_final: categoryFinal,
        };

        if (reason) {
            payload.priority_change_reason = reason;
        }

        return this.request(`/tickets/${id}/triage/resolve`, {
            method: 'PATCH',
            body: JSON.stringify(payload),
        });
    }

    async getMlLogs({
        limit = 50,
        offset = 0,
        ticketId = null,
        ticketFrom = null,
        ticketTo = null,
        feedbackType = 'all',
        priorityPair = 'all',
    } = {}) {
        const params = new URLSearchParams({
            limit,
            offset,
            feedback_type: feedbackType,
            priority_pair: priorityPair,
        });

        if (ticketId) {
            params.append('ticket_id', ticketId);
        }
        if (!ticketId && ticketFrom) {
            params.append('ticket_from', ticketFrom);
        }
        if (!ticketId && ticketTo) {
            params.append('ticket_to', ticketTo);
        }

        return this.request(`/ml/logs?${params.toString()}`);
    }

    // ML Training
    async getTrainingStatus() {
        return this.request('/ml/training/status');
    }

    async triggerTraining(force = false) {
        const params = force ? '?force=true' : '';
        return this.request(`/ml/training/trigger${params}`, {
            method: 'POST',
            body: JSON.stringify({}),
        });
    }

    async getModels(limit = 20) {
        return this.request(`/ml/training/models?limit=${limit}`);
    }

    async getModel(version) {
        return this.request(`/ml/training/models/${version}`);
    }

    async activateModel(version) {
        return this.request(`/ml/training/models/${version}/activate`, {
            method: 'POST',
            body: JSON.stringify({}),
        });
    }

    async getTrainingJobs({ limit = 20, status = null } = {}) {
        const params = new URLSearchParams({ limit });
        if (status) {
            params.append('status', status);
        }
        return this.request(`/ml/training/jobs?${params.toString()}`);
    }

    async getTrainingJob(jobId) {
        return this.request(`/ml/training/jobs/${jobId}`);
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
const API_BASE_URL = API_BASE;  // Export for direct use in HTML files

console.debug('[API] Base URL:', API_BASE);
