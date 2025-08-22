/**
 * Services tab functionality
 * Handles specific service monitoring and management
 */

let servicesData = {
    targetServices: {},
    allContainers: [],
    selectedServices: new Set(),
    lastUpdate: null
};

const TARGET_SERVICES = [
    'sabnzbd', 'qbittorrent', 'sonarr', 'radarr', 'jackett', 'plex',
    'portainer', 'netdata', 'heimdall', 'glances'
];

/**
 * Initialize services tab
 */
function initServicesTab() {
    loadServicesData();
    setupServiceActions();
    
    // Auto-refresh every 10 seconds when tab is active
    setInterval(() => {
        if (currentTab === 'services') {
            loadServicesData();
        }
    }, 10000);
}

/**
 * Load services data
 */
async function loadServicesData() {
    try {
        showLoadingState('services-grid', true);
        
        const data = await makeRequest('/api/containers/');
        servicesData.allContainers = data.data || [];
        
        mapServicesToContainers();
        renderServices();
        updateServicesStats();
        
        servicesData.lastUpdate = new Date();
        updateLastUpdateTime('services-last-update');
        
    } catch (error) {
        console.error('Failed to load services data:', error);
        showToast('Failed to load services data', 'error');
        servicesData.allContainers = [];
        renderServices();
    }
}

/**
 * Map target services to their containers
 */
function mapServicesToContainers() {
    servicesData.targetServices = {};
    
    TARGET_SERVICES.forEach(serviceName => {
        // Find container by name (case insensitive)
        const container = servicesData.allContainers.find(c => 
            c.name.toLowerCase().includes(serviceName.toLowerCase())
        );
        
        servicesData.targetServices[serviceName] = {
            name: serviceName,
            container: container || null,
            isRunning: container ? container.is_running : false,
            isHealthy: container ? container.is_healthy : false,
            uptime: container ? container.uptime : null,
            stats: container ? container.stats : null,
            ports: container ? container.ports : [],
            primaryPort: container ? container.primary_port : null
        };
    });
}

/**
 * Render services grid
 */
function renderServices() {
    const container = document.getElementById('services-grid');
    if (!container) return;
    
    const servicesHTML = TARGET_SERVICES.map(serviceName => {
        const service = servicesData.targetServices[serviceName];
        return getServiceCardHTML(service);
    }).join('');
    
    container.innerHTML = servicesHTML;
}

/**
 * Get HTML for service card
 */
function getServiceCardHTML(service) {
    const isSelected = servicesData.selectedServices.has(service.name);
    const statusColor = service.isRunning ? 'text-green-600' : 'text-red-600';
    const statusBg = service.isRunning ? 'bg-green-100 dark:bg-green-900' : 'bg-red-100 dark:bg-red-900';
    const statusText = service.isRunning ? 'Running' : 'Stopped';
    const healthColor = service.isHealthy ? 'text-green-600' : 'text-yellow-600';
    const healthIcon = service.isHealthy ? 'check-circle' : 'exclamation-circle';
    
    // Get service icon and color
    const serviceConfig = getServiceConfig(service.name);
    
    return `
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-all duration-200 ${isSelected ? 'ring-2 ring-blue-500' : ''} ${!service.container ? 'opacity-75' : ''}">
            <!-- Header -->
            <div class="flex items-center justify-between mb-4">
                <div class="flex items-center space-x-3">
                    <input type="checkbox" ${isSelected ? 'checked' : ''} 
                           ${!service.container ? 'disabled' : ''}
                           onchange="toggleServiceSelection('${service.name}')"
                           class="rounded border-gray-300 text-blue-600 focus:ring-blue-500">
                    <div class="flex items-center space-x-2">
                        <i class="fas fa-${serviceConfig.icon} text-2xl ${serviceConfig.color}"></i>
                        <div>
                            <h3 class="text-lg font-semibold text-gray-900 dark:text-white capitalize">${service.name}</h3>
                            <p class="text-sm text-gray-500 dark:text-gray-400">
                                ${service.container ? service.container.name : 'Container not found'}
                            </p>
                        </div>
                    </div>
                </div>
                ${service.container ? `
                    <button onclick="showServiceActionMenu('${service.name}')" 
                            class="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700">
                        <i class="fas fa-ellipsis-v text-gray-400"></i>
                    </button>
                ` : ''}
            </div>
            
            ${service.container ? `
                <!-- Status and Health -->
                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div>
                        <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-1">Status</p>
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusBg} ${statusColor}">
                            <i class="fas fa-${service.isRunning ? 'play' : 'stop'} mr-1"></i>
                            ${statusText}
                        </span>
                    </div>
                    <div>
                        <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-1">Health</p>
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${service.isHealthy ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'}">
                            <i class="fas fa-${healthIcon} mr-1 ${healthColor}"></i>
                            ${service.isHealthy ? 'Healthy' : 'Unhealthy'}
                        </span>
                    </div>
                </div>
                
                <!-- Service Details -->
                <div class="space-y-2 mb-4">
                    ${service.uptime ? `
                        <div class="flex justify-between items-center">
                            <span class="text-sm text-gray-500 dark:text-gray-400">Uptime:</span>
                            <span class="text-sm text-gray-900 dark:text-white">${service.uptime}</span>
                        </div>
                    ` : ''}
                    
                    ${service.primaryPort ? `
                        <div class="flex justify-between items-center">
                            <span class="text-sm text-gray-500 dark:text-gray-400">Primary Port:</span>
                            <span class="text-sm text-gray-900 dark:text-white">${service.primaryPort}</span>
                        </div>
                    ` : ''}
                    
                    ${service.stats ? `
                        <div class="flex justify-between items-center">
                            <span class="text-sm text-gray-500 dark:text-gray-400">CPU Usage:</span>
                            <span class="text-sm text-gray-900 dark:text-white">${service.stats.cpu_percent.toFixed(1)}%</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-sm text-gray-500 dark:text-gray-400">Memory:</span>
                            <span class="text-sm text-gray-900 dark:text-white">${service.stats.memory_percent.toFixed(1)}%</span>
                        </div>
                    ` : ''}
                </div>
                
                <!-- Ports -->
                ${service.ports.length > 0 ? `
                    <div class="mb-4">
                        <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-2">Ports</p>
                        <div class="flex flex-wrap gap-1">
                            ${service.ports.map(port => `
                                <span class="inline-flex items-center px-2 py-1 rounded text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300">
                                    ${port}
                                </span>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <!-- Quick Actions -->
                <div class="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-600">
                    <div class="flex space-x-2">
                        ${service.isRunning ? `
                            <button onclick="stopService('${service.name}')" 
                                    class="px-3 py-1.5 text-xs bg-red-600 text-white rounded hover:bg-red-700 transition-colors">
                                <i class="fas fa-stop mr-1"></i>Stop
                            </button>
                            <button onclick="restartService('${service.name}')" 
                                    class="px-3 py-1.5 text-xs bg-orange-600 text-white rounded hover:bg-orange-700 transition-colors">
                                <i class="fas fa-redo mr-1"></i>Restart
                            </button>
                        ` : `
                            <button onclick="startService('${service.name}')" 
                                    class="px-3 py-1.5 text-xs bg-green-600 text-white rounded hover:bg-green-700 transition-colors">
                                <i class="fas fa-play mr-1"></i>Start
                            </button>
                        `}
                    </div>
                    <div class="flex space-x-2">
                        ${service.primaryPort && service.isRunning ? `
                            <button onclick="openService('${service.name}', '${service.primaryPort}')" 
                                    class="px-3 py-1.5 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors">
                                <i class="fas fa-external-link-alt mr-1"></i>Open
                            </button>
                        ` : ''}
                        <button onclick="showServiceLogs('${service.name}')" 
                                class="px-3 py-1.5 text-xs bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors">
                            <i class="fas fa-file-alt mr-1"></i>Logs
                        </button>
                    </div>
                </div>
            ` : `
                <!-- Container Not Found -->
                <div class="text-center py-8">
                    <i class="fas fa-exclamation-triangle text-4xl text-yellow-500 mb-3"></i>
                    <p class="text-gray-600 dark:text-gray-400 mb-2">Container not found</p>
                    <p class="text-sm text-gray-500 dark:text-gray-400">
                        No container matching "${service.name}" was found on the host.
                    </p>
                </div>
            `}
        </div>
    `;
}

/**
 * Get service configuration (icon and color)
 */
function getServiceConfig(serviceName) {
    const configs = {
        sabnzbd: { icon: 'download', color: 'text-blue-600' },
        qbittorrent: { icon: 'magnet', color: 'text-blue-600' },
        sonarr: { icon: 'tv', color: 'text-purple-600' },
        radarr: { icon: 'film', color: 'text-yellow-600' },
        jackett: { icon: 'search', color: 'text-green-600' },
        plex: { icon: 'play-circle', color: 'text-orange-600' },
        portainer: { icon: 'docker', color: 'text-blue-600' },
        netdata: { icon: 'chart-line', color: 'text-green-600' },
        heimdall: { icon: 'th-large', color: 'text-orange-600' },
        glances: { icon: 'tachometer-alt', color: 'text-red-600' }
    };
    
    return configs[serviceName] || { icon: 'cube', color: 'text-gray-600' };
}

/**
 * Setup service actions
 */
function setupServiceActions() {
    const bulkActions = document.getElementById('bulk-services-actions');
    const selectAllCheckbox = document.getElementById('select-all-services');
    
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            if (this.checked) {
                TARGET_SERVICES.forEach(serviceName => {
                    const service = servicesData.targetServices[serviceName];
                    if (service && service.container) {
                        servicesData.selectedServices.add(serviceName);
                    }
                });
            } else {
                servicesData.selectedServices.clear();
            }
            renderServices();
            updateBulkServicesVisibility();
        });
    }
}

/**
 * Toggle service selection
 */
function toggleServiceSelection(serviceName) {
    if (servicesData.selectedServices.has(serviceName)) {
        servicesData.selectedServices.delete(serviceName);
    } else {
        servicesData.selectedServices.add(serviceName);
    }
    
    updateBulkServicesVisibility();
    updateSelectAllServicesCheckbox();
}

/**
 * Update bulk actions visibility
 */
function updateBulkServicesVisibility() {
    const bulkActions = document.getElementById('bulk-services-actions');
    const selectedCount = document.getElementById('selected-services-count');
    
    if (bulkActions && selectedCount) {
        const count = servicesData.selectedServices.size;
        
        if (count > 0) {
            bulkActions.classList.remove('hidden');
            selectedCount.textContent = count;
        } else {
            bulkActions.classList.add('hidden');
        }
    }
}

/**
 * Update select all checkbox
 */
function updateSelectAllServicesCheckbox() {
    const selectAllCheckbox = document.getElementById('select-all-services');
    
    if (selectAllCheckbox) {
        const availableServices = TARGET_SERVICES.filter(serviceName => {
            const service = servicesData.targetServices[serviceName];
            return service && service.container;
        });
        
        const selectedCount = servicesData.selectedServices.size;
        const totalAvailable = availableServices.length;
        
        selectAllCheckbox.checked = totalAvailable > 0 && selectedCount === totalAvailable;
        selectAllCheckbox.indeterminate = selectedCount > 0 && selectedCount < totalAvailable;
    }
}

/**
 * Update services statistics
 */
function updateServicesStats() {
    const stats = {
        total: TARGET_SERVICES.length,
        running: 0,
        healthy: 0,
        found: 0
    };
    
    TARGET_SERVICES.forEach(serviceName => {
        const service = servicesData.targetServices[serviceName];
        if (service.container) {
            stats.found++;
            if (service.isRunning) stats.running++;
            if (service.isHealthy) stats.healthy++;
        }
    });
    
    // Update UI
    const elements = {
        'services-total-count': stats.total,
        'services-found-count': stats.found,
        'services-running-count': stats.running,
        'services-healthy-count': stats.healthy
    };
    
    Object.entries(elements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    });
}

// Service Actions
async function startService(serviceName) {
    const service = servicesData.targetServices[serviceName];
    if (!service || !service.container) return;
    
    try {
        await makeRequest(`/api/containers/${service.container.id}/start`, { method: 'POST' });
        showToast(`${serviceName} started successfully`, 'success');
        await loadServicesData();
    } catch (error) {
        console.error(`Failed to start ${serviceName}:`, error);
        showToast(`Failed to start ${serviceName}`, 'error');
    }
}

async function stopService(serviceName) {
    const service = servicesData.targetServices[serviceName];
    if (!service || !service.container) return;
    
    try {
        await makeRequest(`/api/containers/${service.container.id}/stop`, { method: 'POST' });
        showToast(`${serviceName} stopped successfully`, 'success');
        await loadServicesData();
    } catch (error) {
        console.error(`Failed to stop ${serviceName}:`, error);
        showToast(`Failed to stop ${serviceName}`, 'error');
    }
}

async function restartService(serviceName) {
    const service = servicesData.targetServices[serviceName];
    if (!service || !service.container) return;
    
    try {
        await makeRequest(`/api/containers/${service.container.id}/restart`, { method: 'POST' });
        showToast(`${serviceName} restarted successfully`, 'success');
        await loadServicesData();
    } catch (error) {
        console.error(`Failed to restart ${serviceName}:`, error);
        showToast(`Failed to restart ${serviceName}`, 'error');
    }
}

function openService(serviceName, port) {
    // Open service in new tab/window
    const url = `http://logan-GL502VS:${port}`;
    window.open(url, '_blank');
}

function showServiceLogs(serviceName) {
    // Show logs tab with specific service
    showTab('logs');
    if (typeof setLogContainer === 'function') {
        const service = servicesData.targetServices[serviceName];
        if (service && service.container) {
            setLogContainer(service.container.id);
        }
    }
}

function showServiceActionMenu(serviceName) {
    // This will be implemented with a dropdown menu
    console.log('Show service action menu:', serviceName);
}

// Bulk Actions for Services
async function startSelectedServices() {
    if (servicesData.selectedServices.size === 0) return;
    
    try {
        const containerIds = [];
        servicesData.selectedServices.forEach(serviceName => {
            const service = servicesData.targetServices[serviceName];
            if (service && service.container) {
                containerIds.push(service.container.id);
            }
        });
        
        if (containerIds.length > 0) {
            await makeRequest('/api/containers/bulk/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ container_ids: containerIds })
            });
            
            showToast(`Started ${containerIds.length} services`, 'success');
            servicesData.selectedServices.clear();
            updateBulkServicesVisibility();
            await loadServicesData();
        }
    } catch (error) {
        console.error('Failed to start services:', error);
        showToast('Failed to start some services', 'error');
    }
}

async function stopSelectedServices() {
    if (servicesData.selectedServices.size === 0) return;
    
    try {
        const containerIds = [];
        servicesData.selectedServices.forEach(serviceName => {
            const service = servicesData.targetServices[serviceName];
            if (service && service.container) {
                containerIds.push(service.container.id);
            }
        });
        
        if (containerIds.length > 0) {
            await makeRequest('/api/containers/bulk/stop', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ container_ids: containerIds })
            });
            
            showToast(`Stopped ${containerIds.length} services`, 'success');
            servicesData.selectedServices.clear();
            updateBulkServicesVisibility();
            await loadServicesData();
        }
    } catch (error) {
        console.error('Failed to stop services:', error);
        showToast('Failed to stop some services', 'error');
    }
}

async function restartSelectedServices() {
    if (servicesData.selectedServices.size === 0) return;
    
    try {
        const containerIds = [];
        servicesData.selectedServices.forEach(serviceName => {
            const service = servicesData.targetServices[serviceName];
            if (service && service.container) {
                containerIds.push(service.container.id);
            }
        });
        
        if (containerIds.length > 0) {
            await makeRequest('/api/containers/bulk/restart', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ container_ids: containerIds })
            });
            
            showToast(`Restarted ${containerIds.length} services`, 'success');
            servicesData.selectedServices.clear();
            updateBulkServicesVisibility();
            await loadServicesData();
        }
    } catch (error) {
        console.error('Failed to restart services:', error);
        showToast('Failed to restart some services', 'error');
    }
}

/**
 * Refresh services data manually
 */
async function refreshServicesData() {
    try {
        showLoadingSpinner(true);
        await loadServicesData();
        showToast('Services data refreshed', 'success');
    } catch (error) {
        console.error('Failed to refresh services data:', error);
        showToast('Failed to refresh services data', 'error');
    } finally {
        showLoadingSpinner(false);
    }
}

/**
 * Update last update time display
 */
function updateLastUpdateTime(elementId) {
    const element = document.getElementById(elementId);
    if (element && servicesData.lastUpdate) {
        element.textContent = servicesData.lastUpdate.toLocaleTimeString();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (typeof currentTab !== 'undefined' && currentTab === 'services') {
        initServicesTab();
    }
});

// WebSocket handlers for services
if (typeof io !== 'undefined') {
    document.addEventListener('DOMContentLoaded', function() {
        if (typeof socket !== 'undefined' && socket) {
            socket.on('container_update', function(data) {
                if (currentTab === 'services') {
                    servicesData.allContainers = data.containers || [];
                    mapServicesToContainers();
                    renderServices();
                    updateServicesStats();
                }
            });
        }
    });
}
