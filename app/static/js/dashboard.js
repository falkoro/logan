/**
 * Docker Dashboard Main JavaScript
 */
class DockerDashboard {
    constructor() {
        this.containers = new Map();
        this.services = new Map();
        this.autoRefresh = false;
        this.refreshInterval = null;
        this.lastUpdate = null;
        this.activityLog = [];
    }

    /**
     * Initialize dashboard
     */
    async init() {
        console.log('Initializing Docker Dashboard...');
        
        try {
            // Load services configuration
            await this.loadServices();
            
            // Initial data load
            await this.refreshAll();
            
            // Set up auto-refresh if enabled
            if (this.autoRefresh) {
                this.startAutoRefresh();
            }
            
            this.logActivity('Dashboard initialized successfully');
        } catch (error) {
            console.error('Dashboard initialization failed:', error);
            Utils.showToast('Failed to initialize dashboard: ' + error.message, 'error');
        }
    }

    /**
     * Load services configuration
     */
    async loadServices() {
        try {
            if (window.MANAGED_SERVICES) {
                // Use services passed from template
                Object.entries(window.MANAGED_SERVICES).forEach(([key, service]) => {
                    this.services.set(key, { ...service, key });
                });
            } else {
                // Fallback: load from API
                const response = await API.getServices();
                Object.entries(response.data).forEach(([key, service]) => {
                    this.services.set(key, { ...service, key });
                });
            }
            
            console.log(`Loaded ${this.services.size} managed services`);
        } catch (error) {
            console.error('Failed to load services:', error);
            throw error;
        }
    }

    /**
     * Refresh all dashboard data
     */
    async refreshAll() {
        showLoading('Refreshing dashboard data...');
        
        try {
            // Run all refresh operations in parallel
            const promises = [
                this.updateSystemStatus(),
                this.updateSystemMetrics(),
                this.updateServiceHealth(),
                this.updateManagedContainers()
            ];
            
            await Promise.allSettled(promises);
            this.lastUpdate = new Date();
            
        } catch (error) {
            console.error('Dashboard refresh failed:', error);
            Utils.showToast('Dashboard refresh failed: ' + error.message, 'error');
        } finally {
            hideLoading();
        }
    }

    /**
     * Update system status
     */
    async updateSystemStatus() {
        try {
            const response = await API.getSystemStatus();
            const status = response.data;
            
            // Update system health indicator
            const healthElement = document.getElementById('system-health-status');
            if (healthElement) {
                const dot = healthElement.querySelector('.status-dot');
                const text = healthElement.querySelector('span');
                
                dot.className = `status-dot ${status.overall_status}`;
                text.textContent = status.overall_status.charAt(0).toUpperCase() + status.overall_status.slice(1);
            }
            
            // Update service summary
            this.updateServiceSummary(status.services);
            
        } catch (error) {
            console.error('Failed to update system status:', error);
        }
    }

    /**
     * Update system metrics
     */
    async updateSystemMetrics() {
        try {
            const response = await API.getSystemMetrics();
            const metrics = response.data;
            
            // Update resource bars
            this.updateResourceBar('cpu', metrics.cpu_percent);
            this.updateResourceBar('memory', metrics.memory_percent);
            this.updateResourceBar('disk', metrics.disk_percent);
            
        } catch (error) {
            console.error('Failed to update system metrics:', error);
        }
    }

    /**
     * Update resource progress bar
     * @param {string} resource 
     * @param {number} percent 
     */
    updateResourceBar(resource, percent) {
        const progressBar = document.getElementById(`${resource}-progress`);
        const progressText = document.getElementById(`${resource}-text`);
        
        if (progressBar && progressText) {
            progressBar.style.width = `${percent}%`;
            progressText.textContent = `${percent.toFixed(1)}%`;
            
            // Update color based on usage
            progressBar.className = 'progress-fill';
            if (percent > 90) {
                progressBar.style.backgroundColor = 'var(--danger-color)';
            } else if (percent > 75) {
                progressBar.style.backgroundColor = 'var(--warning-color)';
            } else {
                progressBar.style.backgroundColor = 'var(--success-color)';
            }
        }
    }

    /**
     * Update service summary
     * @param {Object} serviceSummary 
     */
    updateServiceSummary(serviceSummary) {
        const totalElement = document.getElementById('total-services');
        const healthyElement = document.getElementById('healthy-services');
        const unhealthyElement = document.getElementById('unhealthy-services');
        
        if (totalElement) totalElement.textContent = serviceSummary.total || 0;
        if (healthyElement) healthyElement.textContent = serviceSummary.healthy || 0;
        if (unhealthyElement) unhealthyElement.textContent = serviceSummary.unhealthy || 0;
    }

    /**
     * Update service health
     */
    async updateServiceHealth() {
        try {
            const response = await API.getServiceHealth();
            const healthData = response.data;
            
            // Create a map for quick lookup
            const healthMap = new Map();
            healthData.forEach(health => {
                // Try to match by service name
                for (const [key, service] of this.services) {
                    if (service.name === health.service_name) {
                        healthMap.set(key, health);
                        break;
                    }
                }
            });
            
            this.serviceHealth = healthMap;
            
        } catch (error) {
            console.error('Failed to update service health:', error);
        }
    }

    /**
     * Update managed containers
     */
    async updateManagedContainers() {
        try {
            const response = await API.getManagedContainers();
            const containers = response.data;
            
            // Update containers map
            this.containers.clear();
            containers.forEach(container => {
                this.containers.set(container.name, container);
            });
            
            // Render service cards
            this.renderServiceCards();
            
        } catch (error) {
            console.error('Failed to update managed containers:', error);
        }
    }

    /**
     * Render service cards
     */
    renderServiceCards() {
        const categories = ['media', 'core', 'monitoring', 'gaming'];
        
        categories.forEach(category => {
            const container = document.getElementById(`${category}-services`);
            if (!container) return;
            
            container.innerHTML = '';
            
            // Get services for this category
            const categoryServices = Array.from(this.services.values())
                .filter(service => service.category === category);
            
            categoryServices.forEach(service => {
                const card = this.createServiceCard(service);
                container.appendChild(card);
            });
        });
    }

    /**
     * Create service card element
     * @param {Object} service 
     * @returns {HTMLElement}
     */
    createServiceCard(service) {
        const template = document.getElementById('service-card-template');
        const card = template.content.cloneNode(true);
        
        // Find container for this service
        const container = Array.from(this.containers.values())
            .find(c => c.service_name === service.name || 
                      c.name === service.container_name ||
                      c.name.includes(service.key));
        
        // Get health status
        const health = this.serviceHealth?.get(service.key);
        
        // Fill in service information
        const cardElement = card.querySelector('.service-card');
        cardElement.setAttribute('data-service-key', service.key);
        
        card.querySelector('.service-name').textContent = service.name;
        card.querySelector('.service-description').textContent = service.description;
        card.querySelector('.service-port').textContent = service.port;
        
        // Show VPN indicator if required
        const vpnElement = card.querySelector('.vpn-status');
        if (service.vpn_required) {
            vpnElement.style.display = 'flex';
        }
        
        // Container information
        const containerNameElement = card.querySelector('.container-name strong');
        if (container) {
            containerNameElement.textContent = container.name;
        } else {
            containerNameElement.textContent = service.container_name || 'Not found';
        }
        
        // Status indicator
        const statusDot = card.querySelector('.status-dot');
        const statusText = card.querySelector('.status-text');
        
        if (container && container.is_running) {
            statusDot.className = 'status-dot healthy';
            statusText.textContent = 'Running';
        } else if (container) {
            statusDot.className = 'status-dot unhealthy';
            statusText.textContent = 'Stopped';
        } else {
            statusDot.className = 'status-dot unknown';
            statusText.textContent = 'Unknown';
        }
        
        // Web link
        const webButton = card.querySelector('.web-btn');
        if (container && container.web_url) {
            webButton.href = container.web_url;
            webButton.style.display = 'inline-flex';
        } else {
            webButton.href = `http://${window.SSH_HOST || 'localhost'}:${service.port}`;
            webButton.style.display = 'inline-flex';
        }
        
        // Action buttons
        const startBtn = card.querySelector('.start-btn');
        const restartBtn = card.querySelector('.restart-btn');
        const stopBtn = card.querySelector('.stop-btn');
        const logsBtn = card.querySelector('.logs-btn');
        
        // Store service key on buttons
        [startBtn, restartBtn, stopBtn, logsBtn].forEach(btn => {
            btn.setAttribute('data-service-key', service.key);
            btn.setAttribute('data-container-name', container?.name || service.container_name);
        });
        
        // Enable/disable buttons based on container state
        if (container) {
            if (container.is_running) {
                startBtn.disabled = true;
                restartBtn.disabled = false;
                stopBtn.disabled = false;
            } else {
                startBtn.disabled = false;
                restartBtn.disabled = true;
                stopBtn.disabled = true;
            }
            logsBtn.disabled = false;
        } else {
            startBtn.disabled = true;
            restartBtn.disabled = true;
            stopBtn.disabled = true;
            logsBtn.disabled = true;
        }
        
        return card;
    }

    /**
     * Start service
     * @param {HTMLElement} button 
     */
    async startService(button) {
        const serviceKey = button.getAttribute('data-service-key');
        const containerName = button.getAttribute('data-container-name');
        
        if (!containerName) {
            Utils.showToast('Container name not found', 'error');
            return;
        }
        
        try {
            button.disabled = true;
            Utils.showToast(`Starting ${serviceKey}...`, 'info');
            
            await API.startContainer(containerName);
            
            Utils.showToast(`${serviceKey} started successfully`, 'success');
            this.logActivity(`Started service: ${serviceKey}`);
            
            // Refresh after a short delay
            setTimeout(() => this.updateManagedContainers(), 2000);
            
        } catch (error) {
            console.error('Failed to start service:', error);
            Utils.showToast(`Failed to start ${serviceKey}: ${error.message}`, 'error');
            this.logActivity(`Failed to start service: ${serviceKey} - ${error.message}`);
        } finally {
            button.disabled = false;
        }
    }

    /**
     * Stop service
     * @param {HTMLElement} button 
     */
    async stopService(button) {
        const serviceKey = button.getAttribute('data-service-key');
        const containerName = button.getAttribute('data-container-name');
        
        if (!containerName) {
            Utils.showToast('Container name not found', 'error');
            return;
        }
        
        const confirmed = await Utils.confirmAction(
            `Are you sure you want to stop ${serviceKey}?`,
            'Stop Service'
        );
        
        if (!confirmed) return;
        
        try {
            button.disabled = true;
            Utils.showToast(`Stopping ${serviceKey}...`, 'info');
            
            await API.stopContainer(containerName);
            
            Utils.showToast(`${serviceKey} stopped successfully`, 'success');
            this.logActivity(`Stopped service: ${serviceKey}`);
            
            // Refresh after a short delay
            setTimeout(() => this.updateManagedContainers(), 2000);
            
        } catch (error) {
            console.error('Failed to stop service:', error);
            Utils.showToast(`Failed to stop ${serviceKey}: ${error.message}`, 'error');
            this.logActivity(`Failed to stop service: ${serviceKey} - ${error.message}`);
        } finally {
            button.disabled = false;
        }
    }

    /**
     * Restart service
     * @param {HTMLElement} button 
     */
    async restartService(button) {
        const serviceKey = button.getAttribute('data-service-key');
        const containerName = button.getAttribute('data-container-name');
        
        if (!containerName) {
            Utils.showToast('Container name not found', 'error');
            return;
        }
        
        try {
            button.disabled = true;
            Utils.showToast(`Restarting ${serviceKey}...`, 'info');
            
            await API.restartContainer(containerName);
            
            Utils.showToast(`${serviceKey} restarted successfully`, 'success');
            this.logActivity(`Restarted service: ${serviceKey}`);
            
            // Refresh after a short delay
            setTimeout(() => this.updateManagedContainers(), 3000);
            
        } catch (error) {
            console.error('Failed to restart service:', error);
            Utils.showToast(`Failed to restart ${serviceKey}: ${error.message}`, 'error');
            this.logActivity(`Failed to restart service: ${serviceKey} - ${error.message}`);
        } finally {
            button.disabled = false;
        }
    }

    /**
     * Show service logs
     * @param {HTMLElement} button 
     */
    async showServiceLogs(button) {
        const serviceKey = button.getAttribute('data-service-key');
        const containerName = button.getAttribute('data-container-name');
        
        if (!containerName) {
            Utils.showToast('Container name not found', 'error');
            return;
        }
        
        try {
            Utils.showLoading(`Loading logs for ${serviceKey}...`);
            
            const response = await API.getContainerLogs(containerName, 50);
            const logs = response.data.logs;
            
            this.showLogsModal(serviceKey, logs);
            
        } catch (error) {
            console.error('Failed to get service logs:', error);
            Utils.showToast(`Failed to get logs for ${serviceKey}: ${error.message}`, 'error');
        } finally {
            Utils.hideLoading();
        }
    }

    /**
     * Show logs in modal
     * @param {string} serviceName 
     * @param {string} logs 
     */
    showLogsModal(serviceName, logs) {
        const modal = document.createElement('div');
        modal.className = 'logs-modal';
        modal.innerHTML = `
            <div class="logs-overlay" onclick="this.parentElement.remove()"></div>
            <div class="logs-dialog">
                <div class="logs-header">
                    <h3>Logs: ${serviceName}</h3>
                    <button class="btn btn-secondary" onclick="this.parentElement.parentElement.remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="logs-body">
                    <pre class="logs-content">${Utils.escapeHtml(logs || 'No logs available')}</pre>
                </div>
                <div class="logs-footer">
                    <button class="btn btn-secondary" onclick="Utils.copyToClipboard(\`${logs}\`).then(() => Utils.showToast('Logs copied to clipboard', 'success'))">
                        <i class="fas fa-copy"></i> Copy
                    </button>
                </div>
            </div>
        `;
        
        // Modal styles
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 1001;
            display: flex;
            justify-content: center;
            align-items: center;
        `;
        
        document.body.appendChild(modal);
    }

    /**
     * Start all services in category
     * @param {string} category 
     */
    async startCategoryServices(category) {
        const services = Array.from(this.services.values())
            .filter(service => service.category === category);
        
        const containerNames = services
            .map(service => {
                const container = Array.from(this.containers.values())
                    .find(c => c.service_name === service.name || 
                              c.name === service.container_name ||
                              c.name.includes(service.key));
                return container?.name || service.container_name;
            })
            .filter(name => name);
        
        if (containerNames.length === 0) {
            Utils.showToast(`No containers found for ${category} services`, 'warning');
            return;
        }
        
        try {
            Utils.showLoading(`Starting ${category} services...`);
            
            const response = await API.bulkContainerAction('start', containerNames);
            
            if (response.status === 'success') {
                Utils.showToast(`All ${category} services started successfully`, 'success');
            } else {
                Utils.showToast(`${response.data.summary.successful} of ${response.data.summary.total} ${category} services started`, 'warning');
            }
            
            this.logActivity(`Bulk start: ${category} services`);
            
            // Refresh after delay
            setTimeout(() => this.updateManagedContainers(), 3000);
            
        } catch (error) {
            console.error('Failed to start category services:', error);
            Utils.showToast(`Failed to start ${category} services: ${error.message}`, 'error');
        } finally {
            Utils.hideLoading();
        }
    }

    /**
     * Stop all services in category
     * @param {string} category 
     */
    async stopCategoryServices(category) {
        const confirmed = await Utils.confirmAction(
            `Are you sure you want to stop all ${category} services?`,
            'Stop Category Services'
        );
        
        if (!confirmed) return;
        
        const services = Array.from(this.services.values())
            .filter(service => service.category === category);
        
        const containerNames = services
            .map(service => {
                const container = Array.from(this.containers.values())
                    .find(c => c.service_name === service.name || 
                              c.name === service.container_name ||
                              c.name.includes(service.key));
                return container?.name || service.container_name;
            })
            .filter(name => name);
        
        if (containerNames.length === 0) {
            Utils.showToast(`No containers found for ${category} services`, 'warning');
            return;
        }
        
        try {
            Utils.showLoading(`Stopping ${category} services...`);
            
            const response = await API.bulkContainerAction('stop', containerNames);
            
            if (response.status === 'success') {
                Utils.showToast(`All ${category} services stopped successfully`, 'success');
            } else {
                Utils.showToast(`${response.data.summary.successful} of ${response.data.summary.total} ${category} services stopped`, 'warning');
            }
            
            this.logActivity(`Bulk stop: ${category} services`);
            
            // Refresh after delay
            setTimeout(() => this.updateManagedContainers(), 2000);
            
        } catch (error) {
            console.error('Failed to stop category services:', error);
            Utils.showToast(`Failed to stop ${category} services: ${error.message}`, 'error');
        } finally {
            Utils.hideLoading();
        }
    }

    /**
     * Toggle auto refresh
     */
    toggleAutoRefresh() {
        this.autoRefresh = !this.autoRefresh;
        
        const button = document.getElementById('auto-refresh-text');
        if (button) {
            button.textContent = this.autoRefresh ? 'Disable Auto Refresh' : 'Enable Auto Refresh';
        }
        
        if (this.autoRefresh) {
            this.startAutoRefresh();
            Utils.showToast('Auto refresh enabled', 'success');
        } else {
            this.stopAutoRefresh();
            Utils.showToast('Auto refresh disabled', 'info');
        }
    }

    /**
     * Start auto refresh
     */
    startAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        this.refreshInterval = setInterval(() => {
            this.refreshAll();
        }, 30000); // Refresh every 30 seconds
    }

    /**
     * Stop auto refresh
     */
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    /**
     * Update connection status
     */
    async updateConnectionStatus() {
        const statusElement = document.getElementById('connection-status');
        if (!statusElement) return;
        
        try {
            const response = await API.healthCheck();
            
            if (response.status === 'healthy') {
                statusElement.className = 'nav-status connected';
                statusElement.querySelector('span').textContent = 'Connected';
            } else {
                statusElement.className = 'nav-status disconnected';
                statusElement.querySelector('span').textContent = 'Issues Detected';
            }
        } catch (error) {
            statusElement.className = 'nav-status disconnected';
            statusElement.querySelector('span').textContent = 'Disconnected';
        }
    }

    /**
     * Log activity
     * @param {string} message 
     */
    logActivity(message) {
        const activity = {
            timestamp: new Date(),
            message: message
        };
        
        this.activityLog.unshift(activity);
        
        // Keep only last 50 activities
        if (this.activityLog.length > 50) {
            this.activityLog = this.activityLog.slice(0, 50);
        }
        
        this.updateActivityLog();
    }

    /**
     * Update activity log display
     */
    updateActivityLog() {
        const logElement = document.getElementById('activity-log');
        if (!logElement) return;
        
        logElement.innerHTML = '';
        
        this.activityLog.forEach(activity => {
            const item = document.createElement('div');
            item.className = 'activity-item';
            item.innerHTML = `
                <span class="activity-time">${Utils.formatRelativeTime(activity.timestamp)}</span>
                <span class="activity-message">${Utils.escapeHtml(activity.message)}</span>
            `;
            logElement.appendChild(item);
        });
    }

    /**
     * Clear activity log
     */
    clearActivityLog() {
        this.activityLog = [];
        this.updateActivityLog();
        Utils.showToast('Activity log cleared', 'info');
    }
}

// Create global dashboard instance
const Dashboard = new DockerDashboard();

// Export for global access
window.Dashboard = Dashboard;

// Add CSS for modals
const modalStyles = document.createElement('style');
modalStyles.textContent = `
    .logs-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0,0,0,0.5);
    }
    
    .logs-dialog {
        background: white;
        border-radius: 8px;
        width: 90vw;
        max-width: 800px;
        max-height: 90vh;
        display: flex;
        flex-direction: column;
        position: relative;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .logs-header {
        padding: 1rem 1.5rem;
        border-bottom: 1px solid #dee2e6;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .logs-header h3 {
        margin: 0;
        color: #343a40;
    }
    
    .logs-body {
        flex: 1;
        overflow: hidden;
        padding: 1rem;
    }
    
    .logs-content {
        width: 100%;
        height: 400px;
        background-color: #2d3748;
        color: #e2e8f0;
        padding: 1rem;
        margin: 0;
        border-radius: 4px;
        overflow: auto;
        font-family: 'Courier New', monospace;
        font-size: 0.8rem;
        line-height: 1.4;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    
    .logs-footer {
        padding: 1rem 1.5rem;
        border-top: 1px solid #dee2e6;
        display: flex;
        gap: 1rem;
        justify-content: flex-end;
    }
`;
document.head.appendChild(modalStyles);
