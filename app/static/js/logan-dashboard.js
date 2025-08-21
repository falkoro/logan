/**
 * Logan Dashboard - 1080p Optimized JavaScript
 */
class LoganDashboard {
    constructor() {
        this.containers = new Map();
        this.services = new Map();
        this.autoRefresh = false;
        this.refreshInterval = null;
        this.lastUpdate = null;
        this.activityLog = [];
        this.metricsChart = null;
        this.metrics = {
            cpu: [],
            memory: [],
            timestamps: []
        };
    }

    /**
     * Initialize dashboard
     */
    async init() {
        console.log('Initializing Logan Dashboard...');
        
        try {
            // Load services configuration
            await this.loadServices();
            
            // Initialize charts
            this.initializeCharts();
            
            // Initial data load
            await this.refreshAll();
            
            // Set up auto-refresh
            this.startAutoRefresh();
            
            this.logActivity('Logan Dashboard initialized successfully', 'success');
        } catch (error) {
            console.error('Dashboard initialization failed:', error);
            this.showToast('Failed to initialize dashboard: ' + error.message, 'error');
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
                const response = await ApiClient.getServices();
                Object.entries(response.services).forEach(([key, service]) => {
                    this.services.set(key, { ...service, key });
                });
            }
        } catch (error) {
            console.error('Failed to load services:', error);
            throw error;
        }
    }

    /**
     * Initialize charts for metrics
     */
    initializeCharts() {
        const ctx = document.getElementById('metricsChart');
        if (!ctx) return;

        this.metricsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.metrics.timestamps,
                datasets: [{
                    label: 'CPU %',
                    data: this.metrics.cpu,
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'Memory %',
                    data: this.metrics.memory,
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    },
                    x: {
                        display: false
                    }
                },
                elements: {
                    point: {
                        radius: 0
                    }
                }
            }
        });
    }

    /**
     * Refresh all dashboard data
     */
    async refreshAll() {
        try {
            await Promise.all([
                this.refreshSystemMetrics(),
                this.refreshServices(),
                this.refreshContainers()
            ]);
            
            this.lastUpdate = new Date();
            this.updateLastUpdateTime();
            
        } catch (error) {
            console.error('Failed to refresh data:', error);
            this.showToast('Failed to refresh data', 'error');
        }
    }

    /**
     * Refresh system metrics
     */
    async refreshSystemMetrics() {
        try {
            const metrics = await ApiClient.getSystemMetrics();
            
            // Update status cards
            this.updateStatusCard('system-health-status', 'Healthy', 'success');
            this.updateStatusCard('cpu-value', Math.round(metrics.cpu_usage) + '%');
            this.updateStatusCard('memory-value', Math.round(metrics.memory_usage) + '%');
            
            // Update metrics chart
            this.updateMetricsChart(metrics);
            
        } catch (error) {
            console.error('Failed to refresh system metrics:', error);
            this.updateStatusCard('system-health-status', 'Error', 'error');
        }
    }

    /**
     * Update status card value
     */
    updateStatusCard(elementId, value, status = 'normal') {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
            element.className = `value ${status}`;
        }
    }

    /**
     * Update metrics chart with new data
     */
    updateMetricsChart(metrics) {
        if (!this.metricsChart) return;

        const now = new Date().toLocaleTimeString();
        
        // Keep only last 20 data points for 1080p optimization
        if (this.metrics.timestamps.length >= 20) {
            this.metrics.timestamps.shift();
            this.metrics.cpu.shift();
            this.metrics.memory.shift();
        }
        
        this.metrics.timestamps.push(now);
        this.metrics.cpu.push(Math.round(metrics.cpu_usage));
        this.metrics.memory.push(Math.round(metrics.memory_usage));
        
        this.metricsChart.update('none');
    }

    /**
     * Refresh services data
     */
    async refreshServices() {
        try {
            const response = await ApiClient.getContainers();
            let runningCount = 0;
            
            // Clear existing services display
            const container = document.getElementById('services-container');
            if (!container) return;
            
            container.innerHTML = '';
            
            // Display each service
            this.services.forEach((service, key) => {
                const container_info = response.containers.find(c => 
                    c.ports.some(p => p.public_port === service.port)
                );
                
                const isRunning = container_info && container_info.status === 'running';
                if (isRunning) runningCount++;
                
                const serviceCard = this.createServiceCard(service, isRunning, container_info);
                container.appendChild(serviceCard);
            });
            
            // Update services count
            this.updateStatusCard('services-count', runningCount);
            
        } catch (error) {
            console.error('Failed to refresh services:', error);
            this.logActivity('Failed to refresh services', 'error');
        }
    }

    /**
     * Create service card element
     */
    createServiceCard(service, isRunning, containerInfo) {
        const card = document.createElement('div');
        card.className = `service-card ${isRunning ? 'running' : 'stopped'}`;
        
        card.innerHTML = `
            <h4>${service.name}</h4>
            <div class="service-port">Port: ${service.port}</div>
            <div class="service-status">
                <div class="status-indicator ${isRunning ? 'status-running' : 'status-stopped'}"></div>
                ${isRunning ? 'Running' : 'Stopped'}
            </div>
            <div class="service-actions">
                <button class="btn btn-success" onclick="Dashboard.startService('${service.key}')" ${isRunning ? 'disabled' : ''}>
                    <i class="fas fa-play"></i> Start
                </button>
                <button class="btn btn-danger" onclick="Dashboard.stopService('${service.key}')" ${!isRunning ? 'disabled' : ''}>
                    <i class="fas fa-stop"></i> Stop
                </button>
                <button class="btn btn-secondary" onclick="Dashboard.restartService('${service.key}')">
                    <i class="fas fa-redo"></i> Restart
                </button>
            </div>
        `;
        
        return card;
    }

    /**
     * Refresh containers data
     */
    async refreshContainers() {
        try {
            const response = await ApiClient.getContainers();
            this.containers.clear();
            
            response.containers.forEach(container => {
                this.containers.set(container.id, container);
            });
            
        } catch (error) {
            console.error('Failed to refresh containers:', error);
        }
    }

    /**
     * Start a service
     */
    async startService(serviceKey) {
        try {
            const service = this.services.get(serviceKey);
            if (!service) return;
            
            this.showToast(`Starting ${service.name}...`, 'info');
            this.logActivity(`Starting service: ${service.name}`, 'info');
            
            await ApiClient.startContainer(service.container_name || service.name);
            
            this.showToast(`${service.name} started successfully`, 'success');
            this.logActivity(`Service started: ${service.name}`, 'success');
            
            // Refresh after a delay
            setTimeout(() => this.refreshServices(), 2000);
            
        } catch (error) {
            console.error('Failed to start service:', error);
            this.showToast(`Failed to start service: ${error.message}`, 'error');
            this.logActivity(`Failed to start service: ${error.message}`, 'error');
        }
    }

    /**
     * Stop a service
     */
    async stopService(serviceKey) {
        try {
            const service = this.services.get(serviceKey);
            if (!service) return;
            
            this.showToast(`Stopping ${service.name}...`, 'info');
            this.logActivity(`Stopping service: ${service.name}`, 'info');
            
            await ApiClient.stopContainer(service.container_name || service.name);
            
            this.showToast(`${service.name} stopped successfully`, 'success');
            this.logActivity(`Service stopped: ${service.name}`, 'success');
            
            // Refresh after a delay
            setTimeout(() => this.refreshServices(), 2000);
            
        } catch (error) {
            console.error('Failed to stop service:', error);
            this.showToast(`Failed to stop service: ${error.message}`, 'error');
            this.logActivity(`Failed to stop service: ${error.message}`, 'error');
        }
    }

    /**
     * Restart a service
     */
    async restartService(serviceKey) {
        try {
            const service = this.services.get(serviceKey);
            if (!service) return;
            
            this.showToast(`Restarting ${service.name}...`, 'info');
            this.logActivity(`Restarting service: ${service.name}`, 'info');
            
            await ApiClient.restartContainer(service.container_name || service.name);
            
            this.showToast(`${service.name} restarted successfully`, 'success');
            this.logActivity(`Service restarted: ${service.name}`, 'success');
            
            // Refresh after a delay
            setTimeout(() => this.refreshServices(), 3000);
            
        } catch (error) {
            console.error('Failed to restart service:', error);
            this.showToast(`Failed to restart service: ${error.message}`, 'error');
            this.logActivity(`Failed to restart service: ${error.message}`, 'error');
        }
    }

    /**
     * Start auto-refresh
     */
    startAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        this.autoRefresh = true;
        this.refreshInterval = setInterval(() => {
            this.refreshAll();
        }, 30000); // Refresh every 30 seconds
        
        this.logActivity('Auto-refresh enabled (30s interval)', 'info');
    }

    /**
     * Stop auto-refresh
     */
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
        
        this.autoRefresh = false;
        this.logActivity('Auto-refresh disabled', 'info');
    }

    /**
     * Toggle auto-refresh
     */
    toggleAutoRefresh() {
        if (this.autoRefresh) {
            this.stopAutoRefresh();
        } else {
            this.startAutoRefresh();
        }
        
        this.updateAutoRefreshButton();
    }

    /**
     * Update auto-refresh button text
     */
    updateAutoRefreshButton() {
        const button = document.getElementById('auto-refresh-text');
        if (button) {
            button.textContent = this.autoRefresh ? 'Disable Auto Refresh' : 'Enable Auto Refresh';
        }
    }

    /**
     * Update last update time display
     */
    updateLastUpdateTime() {
        const element = document.getElementById('last-update');
        if (element && this.lastUpdate) {
            element.textContent = `Last updated: ${this.lastUpdate.toLocaleTimeString()}`;
        }
    }

    /**
     * Log activity
     */
    logActivity(message, type = 'info') {
        const entry = {
            timestamp: new Date(),
            message,
            type
        };
        
        this.activityLog.unshift(entry);
        
        // Keep only last 50 entries for 1080p optimization
        if (this.activityLog.length > 50) {
            this.activityLog = this.activityLog.slice(0, 50);
        }
        
        this.updateActivityLog();
    }

    /**
     * Update activity log display
     */
    updateActivityLog() {
        const container = document.getElementById('activity-log-container');
        if (!container) return;
        
        container.innerHTML = '';
        
        this.activityLog.slice(0, 10).forEach(entry => { // Show only first 10 for 1080p
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry ${entry.type}`;
            
            logEntry.innerHTML = `
                <span class="log-time">${entry.timestamp.toLocaleTimeString()}</span>
                ${entry.message}
            `;
            
            container.appendChild(logEntry);
        });
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        // Simple toast implementation
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'error' ? '#dc3545' : type === 'success' ? '#28a745' : '#007bff'};
            color: white;
            padding: 12px 20px;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 9999;
            font-size: 14px;
            max-width: 300px;
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 4000);
    }
}

// Initialize dashboard when DOM is loaded
let Dashboard;
document.addEventListener('DOMContentLoaded', () => {
    Dashboard = new LoganDashboard();
    Dashboard.init();
});

// Export for global access
window.Dashboard = Dashboard;
