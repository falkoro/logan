/**
 * Dashboard tab functionality
 * Handles the main dashboard overview
 */

let dashboardData = {
    containers: [],
    systemInfo: null,
    lastUpdate: null
};

/**
 * Load dashboard data
 */
async function loadDashboardData() {
    // Use the progressive loading from main.js
    await loadDashboardDataProgressively();
}

/**
 * Load containers for dashboard (legacy support)
 */
async function loadDashboardContainers() {
    try {
        const data = await makeRequest('/api/containers/overview');
        dashboardData.containers = data.data.containers || [];
        dashboardData.lastUpdate = new Date();
        
        updateRunningContainers();
        
    } catch (error) {
        console.error('Failed to load containers for dashboard:', error);
        dashboardData.containers = [];
        loadingManager.showError('running-containers', 'Failed to load containers');
    }
}

/**
 * Load system information for dashboard (legacy support)
 */
async function loadDashboardSystemInfo() {
    try {
        const data = await makeRequest('/api/system/info');
        dashboardData.systemInfo = data.data || null;
        
        updateSystemInfo();
        
    } catch (error) {
        console.error('Failed to load system info for dashboard:', error);
        dashboardData.systemInfo = null;
        loadingManager.showError('system-info', 'Failed to load system information');
    }
}

/**
 * Update dashboard statistics
 */
function updateDashboardStats() {
    const containers = dashboardData.containers;
    
    // Update container count
    const containerCount = document.getElementById('container-count');
    const runningCount = document.getElementById('running-count');
    
    if (containerCount && runningCount) {
        const total = containers.length;
        const running = containers.filter(c => c.is_running).length;
        
        containerCount.textContent = total.toString();
        runningCount.textContent = running.toString();
    }
}

/**
 * Update quick stats (CPU, Memory, Disk)
 */
function updateQuickStats() {
    const systemInfo = dashboardData.systemInfo;
    
    if (!systemInfo) {
        resetQuickStats();
        return;
    }
    
    // CPU Usage
    const cpuUsage = document.getElementById('cpu-usage');
    const cpuProgress = document.getElementById('cpu-progress');
    
    if (cpuUsage && cpuProgress) {
        const cpuPercent = systemInfo.cpu?.percent || 0;
        cpuUsage.textContent = `${cpuPercent.toFixed(1)}%`;
        cpuProgress.style.width = `${Math.min(cpuPercent, 100)}%`;
        
        // Update color based on usage
        cpuProgress.className = 'h-2 rounded-full transition-all duration-300 ' + getCpuColorClass(cpuPercent);
    }
    
    // Memory Usage
    const memoryUsage = document.getElementById('memory-usage');
    const memoryProgress = document.getElementById('memory-progress');
    
    if (memoryUsage && memoryProgress) {
        const memoryPercent = systemInfo.memory?.percent || 0;
        memoryUsage.textContent = `${memoryPercent.toFixed(1)}%`;
        memoryProgress.style.width = `${Math.min(memoryPercent, 100)}%`;
        
        // Update color based on usage
        memoryProgress.className = 'h-2 rounded-full transition-all duration-300 ' + getMemoryColorClass(memoryPercent);
    }
    
    // Disk Usage
    const diskUsage = document.getElementById('disk-usage');
    const diskProgress = document.getElementById('disk-progress');
    
    if (diskUsage && diskProgress) {
        const diskPercent = systemInfo.summary?.disk_usage_percent || 0;
        diskUsage.textContent = `${diskPercent.toFixed(1)}%`;
        diskProgress.style.width = `${Math.min(diskPercent, 100)}%`;
        
        // Update color based on usage
        diskProgress.className = 'h-2 rounded-full transition-all duration-300 ' + getDiskColorClass(diskPercent);
    }
}

/**
 * Reset quick stats to loading state
 */
function resetQuickStats() {
    const elements = [
        'cpu-usage', 'memory-usage', 'disk-usage',
        'cpu-progress', 'memory-progress', 'disk-progress'
    ];
    
    elements.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            if (id.includes('usage')) {
                element.textContent = '-';
            } else if (id.includes('progress')) {
                element.style.width = '0%';
            }
        }
    });
}

/**
 * Get CPU color class based on usage percentage
 */
function getCpuColorClass(percent) {
    if (percent >= 90) return 'bg-red-600';
    if (percent >= 70) return 'bg-orange-600';
    if (percent >= 50) return 'bg-yellow-600';
    return 'bg-blue-600';
}

/**
 * Get Memory color class based on usage percentage
 */
function getMemoryColorClass(percent) {
    if (percent >= 90) return 'bg-red-600';
    if (percent >= 70) return 'bg-orange-600';
    if (percent >= 50) return 'bg-yellow-600';
    return 'bg-purple-600';
}

/**
 * Get Disk color class based on usage percentage
 */
function getDiskColorClass(percent) {
    if (percent >= 95) return 'bg-red-600';
    if (percent >= 80) return 'bg-orange-600';
    if (percent >= 60) return 'bg-yellow-600';
    return 'bg-orange-600';
}

/**
 * Update running containers list
 */
function updateRunningContainers() {
    const container = document.getElementById('running-containers');
    if (!container) return;
    
    const runningContainers = dashboardData.containers.filter(c => c.is_running);
    
    if (runningContainers.length === 0) {
        container.innerHTML = `
            <div class="text-center text-gray-500 dark:text-gray-400 py-4">
                <i class="fas fa-info-circle text-2xl mb-2"></i>
                <p>No containers are currently running</p>
            </div>
        `;
        return;
    }
    
    const containerHTML = runningContainers.map(container => `
        <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors">
            <div class="flex items-center space-x-3">
                <div class="w-3 h-3 rounded-full ${container.is_healthy ? 'bg-green-500' : 'bg-red-500'} animate-pulse-slow"></div>
                <div>
                    <p class="font-medium text-gray-900 dark:text-white">${container.name}</p>
                    <p class="text-sm text-gray-500 dark:text-gray-400">
                        ${container.uptime || 'Unknown uptime'}
                        ${container.primary_port ? ` • Port ${container.primary_port}` : ''}
                    </p>
                </div>
            </div>
            <div class="flex items-center space-x-2">
                ${container.stats ? `
                    <div class="text-xs text-gray-500 dark:text-gray-400">
                        ${container.stats.cpu_percent.toFixed(1)}% CPU
                    </div>
                ` : ''}
                <button onclick="showContainerActions('${container.name}')" class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-500">
                    <i class="fas fa-ellipsis-v text-gray-400"></i>
                </button>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = containerHTML;
}

/**
 * Update system information panel
 */
function updateSystemInfo() {
    const systemInfo = dashboardData.systemInfo;
    
    if (!systemInfo) {
        resetSystemInfo();
        return;
    }
    
    // Update system information fields
    const fields = {
        'system-hostname': systemInfo.hostname || 'Unknown',
        'system-platform': systemInfo.platform || 'Unknown',
        'system-uptime': systemInfo.uptime_formatted || 'Unknown',
        'system-load': systemInfo.cpu?.load_avg?.join(', ') || 'N/A'
    };
    
    Object.entries(fields).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    });
}

/**
 * Reset system info to loading state
 */
function resetSystemInfo() {
    const fields = ['system-hostname', 'system-platform', 'system-uptime', 'system-load'];
    
    fields.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = '-';
        }
    });
}

/**
 * Show container actions dropdown
 */
function showContainerActions(containerName) {
    // This will be implemented with the containers module
    if (typeof showContainerActionMenu === 'function') {
        showContainerActionMenu(containerName);
    } else {
        showTab('containers');
    }
}

/**
 * Refresh dashboard data
 */
async function refreshDashboardData() {
    try {
        showLoadingSpinner(true);
        await loadDashboardData();
        showToast('Dashboard refreshed', 'success');
    } catch (error) {
        console.error('Failed to refresh dashboard:', error);
        showToast('Failed to refresh dashboard', 'error');
    } finally {
        showLoadingSpinner(false);
    }
}

// WebSocket event handlers for dashboard
if (typeof io !== 'undefined') {
    // Request updates when dashboard tab is active
    document.addEventListener('DOMContentLoaded', function() {
        if (typeof socket !== 'undefined' && socket) {
            socket.on('container_update', function(data) {
                if (currentTab === 'dashboard') {
                    dashboardData.containers = data.containers || [];
                    updateDashboardStats();
                    updateRunningContainers();
                }
            });
            
            socket.on('system_update', function(data) {
                if (currentTab === 'dashboard') {
                    dashboardData.systemInfo = data;
                    updateSystemInfo();
                    updateQuickStats();
                }
            });
        }
    });
}

// Auto-refresh dashboard when it becomes active
document.addEventListener('visibilitychange', function() {
    if (!document.hidden && currentTab === 'dashboard') {
        loadDashboardData();
    }
});
