/**
 * API Client for Docker Dashboard
 */
class ApiClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
        };
    }

    /**
     * Make HTTP request
     * @param {string} url 
     * @param {Object} options 
     * @returns {Promise<Object>}
     */
    async request(url, options = {}) {
        const config = {
            headers: { ...this.defaultHeaders, ...options.headers },
            ...options
        };

        try {
            const response = await fetch(this.baseUrl + url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || `HTTP ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    /**
     * GET request
     * @param {string} url 
     * @param {Object} params 
     * @returns {Promise<Object>}
     */
    async get(url, params = {}) {
        const searchParams = new URLSearchParams(params).toString();
        const fullUrl = searchParams ? `${url}?${searchParams}` : url;
        return this.request(fullUrl);
    }

    /**
     * POST request
     * @param {string} url 
     * @param {Object} data 
     * @returns {Promise<Object>}
     */
    async post(url, data = {}) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * PUT request
     * @param {string} url 
     * @param {Object} data 
     * @returns {Promise<Object>}
     */
    async put(url, data = {}) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE request
     * @param {string} url 
     * @returns {Promise<Object>}
     */
    async delete(url) {
        return this.request(url, { method: 'DELETE' });
    }

    // Health Check
    async healthCheck() {
        return this.get('/api/health');
    }

    // System APIs
    async getSystemMetrics(useCache = true) {
        return this.get('/api/system/metrics', { cache: useCache });
    }

    async getSystemInfo() {
        return this.get('/api/system/info');
    }

    async getSystemStatus() {
        return this.get('/api/system/status');
    }

    async getServiceHealth(useCache = true) {
        return this.get('/api/system/health', { cache: useCache });
    }

    async getNetworkInfo() {
        return this.get('/api/system/network');
    }

    async clearCache() {
        return this.post('/api/system/cache/clear');
    }

    // Container APIs
    async getContainers(allContainers = true) {
        return this.get('/api/containers', { all: allContainers });
    }

    async getManagedContainers() {
        return this.get('/api/containers/managed');
    }

    async getContainer(containerName) {
        return this.get(`/api/containers/${encodeURIComponent(containerName)}`);
    }

    async startContainer(containerName) {
        return this.post(`/api/containers/${encodeURIComponent(containerName)}/start`);
    }

    async stopContainer(containerName, timeout = 10) {
        return this.post(`/api/containers/${encodeURIComponent(containerName)}/stop`, { timeout });
    }

    async restartContainer(containerName, timeout = 10) {
        return this.post(`/api/containers/${encodeURIComponent(containerName)}/restart`, { timeout });
    }

    async getContainerLogs(containerName, tail = 100, since = null) {
        const params = { tail };
        if (since) params.since = since;
        return this.get(`/api/containers/${encodeURIComponent(containerName)}/logs`, params);
    }

    async getContainerStats(containerName) {
        return this.get(`/api/containers/${encodeURIComponent(containerName)}/stats`);
    }

    async bulkContainerAction(action, containerNames, timeout = 10) {
        return this.post('/api/containers/bulk/action', {
            action,
            containers: containerNames,
            timeout
        });
    }

    // Services API
    async getServices() {
        return this.get('/api/services');
    }
}

// Create global API client instance
window.API = new ApiClient();
