/**
 * System monitoring tab functionality
 * Handles system metrics and monitoring via Glances API
 */

let systemData = {
    info: null,
    metrics: {
        cpu: [],
        memory: [],
        disk: [],
        network: []
    },
    processes: [],
    lastUpdate: null
};

let systemCharts = {
    cpu: null,
    memory: null,
    network: null
};

/**
 * Initialize system monitoring tab
 */
function initSystemTab() {
    loadSystemData();
    initSystemCharts();
    
    // Auto-refresh every 5 seconds when tab is active
    setInterval(() => {
        if (currentTab === 'system') {
            loadSystemData();
        }
    }, 5000);
}

/**
 * Load system data
 */
async function loadSystemData() {
    try {
        await Promise.all([
            loadSystemInfo(),
            loadSystemMetrics(),
            loadSystemProcesses()
        ]);
        
        updateSystemDisplay();
        updateSystemCharts();
        
        systemData.lastUpdate = new Date();
        updateLastUpdateTime();
        
    } catch (error) {
        console.error('Failed to load system data:', error);
        showToast('Failed to load system data', 'error');
    }
}

/**
 * Load system information
 */
async function loadSystemInfo() {
    try {
        const data = await makeRequest('/api/system/info');
        systemData.info = data.data || null;
    } catch (error) {
        console.error('Failed to load system info:', error);
        systemData.info = null;
    }
}

/**
 * Load system metrics
 */
async function loadSystemMetrics() {
    try {
        const data = await makeRequest('/api/system/metrics');
        const metrics = data.data || {};
        
        // Store latest metrics and maintain history
        if (metrics.cpu) {
            systemData.metrics.cpu.push({
                timestamp: new Date(),
                value: metrics.cpu.percent
            });
            // Keep only last 20 data points
            if (systemData.metrics.cpu.length > 20) {
                systemData.metrics.cpu.shift();
            }
        }
        
        if (metrics.memory) {
            systemData.metrics.memory.push({
                timestamp: new Date(),
                value: metrics.memory.percent
            });
            if (systemData.metrics.memory.length > 20) {
                systemData.metrics.memory.shift();
            }
        }
        
        if (metrics.network) {
            systemData.metrics.network.push({
                timestamp: new Date(),
                rx: metrics.network.rx_per_sec || 0,
                tx: metrics.network.tx_per_sec || 0
            });
            if (systemData.metrics.network.length > 20) {
                systemData.metrics.network.shift();
            }
        }
        
    } catch (error) {
        console.error('Failed to load system metrics:', error);
    }
}

/**
 * Load system processes
 */
async function loadSystemProcesses() {
    try {
        const data = await makeRequest('/api/system/processes');
        systemData.processes = data.data || [];
    } catch (error) {
        console.error('Failed to load system processes:', error);
        systemData.processes = [];
    }
}

/**
 * Update system information display
 */
function updateSystemDisplay() {
    updateSystemOverview();
    updateSystemMetricsDisplay();
    updateProcessesList();
}

/**
 * Update system overview section
 */
function updateSystemOverview() {
    const info = systemData.info;
    if (!info) return;
    
    const fields = {
        'system-overview-hostname': info.hostname || 'Unknown',
        'system-overview-platform': info.platform || 'Unknown',
        'system-overview-uptime': info.uptime_formatted || 'Unknown',
        'system-overview-boot-time': info.boot_time_formatted || 'Unknown',
        'system-overview-load-avg': info.cpu?.load_avg?.join(', ') || 'N/A',
        'system-overview-cpu-cores': info.cpu?.cores || 'Unknown',
        'system-overview-memory-total': formatBytes(info.memory?.total || 0),
        'system-overview-disk-total': formatBytes(info.summary?.disk_total || 0)
    };
    
    Object.entries(fields).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    });
}

/**
 * Update system metrics display
 */
function updateSystemMetricsDisplay() {
    if (systemData.metrics.cpu.length > 0) {
        const latestCpu = systemData.metrics.cpu[systemData.metrics.cpu.length - 1];
        updateMetricCard('cpu-usage-current', `${latestCpu.value.toFixed(1)}%`, latestCpu.value);
    }
    
    if (systemData.metrics.memory.length > 0) {
        const latestMemory = systemData.metrics.memory[systemData.metrics.memory.length - 1];
        updateMetricCard('memory-usage-current', `${latestMemory.value.toFixed(1)}%`, latestMemory.value);
    }
    
    // Update disk usage if available
    if (systemData.info?.summary?.disk_usage_percent !== undefined) {
        const diskUsage = systemData.info.summary.disk_usage_percent;
        updateMetricCard('disk-usage-current', `${diskUsage.toFixed(1)}%`, diskUsage);
    }
    
    // Update network info
    if (systemData.metrics.network.length > 0) {
        const latestNetwork = systemData.metrics.network[systemData.metrics.network.length - 1];
        const element = document.getElementById('network-usage-current');
        if (element) {
            element.textContent = `↓ ${formatBytes(latestNetwork.rx)}/s ↑ ${formatBytes(latestNetwork.tx)}/s`;
        }
    }
}

/**
 * Update metric card with value and progress bar
 */
function updateMetricCard(elementId, text, percentage) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = text;
    }
    
    const progressBar = document.getElementById(elementId + '-progress');
    if (progressBar) {
        progressBar.style.width = `${Math.min(percentage, 100)}%`;
        
        // Update color based on usage
        let colorClass = 'bg-blue-600';
        if (percentage >= 90) colorClass = 'bg-red-600';
        else if (percentage >= 70) colorClass = 'bg-orange-600';
        else if (percentage >= 50) colorClass = 'bg-yellow-600';
        
        progressBar.className = `h-2 rounded-full transition-all duration-300 ${colorClass}`;
    }
}

/**
 * Update processes list
 */
function updateProcessesList() {
    const container = document.getElementById('processes-list');
    if (!container) return;
    
    if (systemData.processes.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8">
                <i class="fas fa-info-circle text-4xl text-gray-300 dark:text-gray-600 mb-2"></i>
                <p class="text-gray-500 dark:text-gray-400">No process information available</p>
            </div>
        `;
        return;
    }
    
    // Sort processes by CPU usage (descending)
    const sortedProcesses = [...systemData.processes]
        .sort((a, b) => (b.cpu_percent || 0) - (a.cpu_percent || 0))
        .slice(0, 10); // Show top 10 processes
    
    const processesHTML = sortedProcesses.map(process => `
        <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
            <td class="px-4 py-3 text-sm text-gray-900 dark:text-white">${process.name || 'N/A'}</td>
            <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">${process.pid || 'N/A'}</td>
            <td class="px-4 py-3 text-sm">
                <div class="flex items-center">
                    <span class="text-gray-900 dark:text-white mr-2">${(process.cpu_percent || 0).toFixed(1)}%</span>
                    <div class="w-16 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                        <div class="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                             style="width: ${Math.min(process.cpu_percent || 0, 100)}%"></div>
                    </div>
                </div>
            </td>
            <td class="px-4 py-3 text-sm">
                <div class="flex items-center">
                    <span class="text-gray-900 dark:text-white mr-2">${(process.memory_percent || 0).toFixed(1)}%</span>
                    <div class="w-16 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                        <div class="bg-purple-600 h-2 rounded-full transition-all duration-300" 
                             style="width: ${Math.min(process.memory_percent || 0, 100)}%"></div>
                    </div>
                </div>
            </td>
            <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">${process.status || 'N/A'}</td>
        </tr>
    `).join('');
    
    container.innerHTML = `
        <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead class="bg-gray-50 dark:bg-gray-700">
                    <tr>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Process</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">PID</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">CPU %</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Memory %</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Status</th>
                    </tr>
                </thead>
                <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    ${processesHTML}
                </tbody>
            </table>
        </div>
    `;
}

/**
 * Initialize system monitoring charts
 */
function initSystemCharts() {
    // Check if Chart.js is available
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js not available, skipping chart initialization');
        return;
    }
    
    initCpuChart();
    initMemoryChart();
    initNetworkChart();
}

/**
 * Initialize CPU usage chart
 */
function initCpuChart() {
    const ctx = document.getElementById('cpu-chart');
    if (!ctx) return;
    
    systemCharts.cpu = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'CPU Usage (%)',
                data: [],
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: 'rgba(156, 163, 175, 0.2)'
                    }
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
 * Initialize Memory usage chart
 */
function initMemoryChart() {
    const ctx = document.getElementById('memory-chart');
    if (!ctx) return;
    
    systemCharts.memory = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Memory Usage (%)',
                data: [],
                borderColor: 'rgb(147, 51, 234)',
                backgroundColor: 'rgba(147, 51, 234, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: 'rgba(156, 163, 175, 0.2)'
                    }
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
 * Initialize Network usage chart
 */
function initNetworkChart() {
    const ctx = document.getElementById('network-chart');
    if (!ctx) return;
    
    systemCharts.network = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Download (bytes/s)',
                    data: [],
                    borderColor: 'rgb(34, 197, 94)',
                    backgroundColor: 'rgba(34, 197, 94, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Upload (bytes/s)',
                    data: [],
                    borderColor: 'rgb(239, 68, 68)',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4
                }
            ]
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
                x: {
                    display: false
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(156, 163, 175, 0.2)'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatBytes(value) + '/s';
                        }
                    }
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
 * Update system charts with latest data
 */
function updateSystemCharts() {
    if (typeof Chart === 'undefined') return;
    
    updateCpuChart();
    updateMemoryChart();
    updateNetworkChart();
}

/**
 * Update CPU chart
 */
function updateCpuChart() {
    if (!systemCharts.cpu || systemData.metrics.cpu.length === 0) return;
    
    const labels = systemData.metrics.cpu.map(item => 
        item.timestamp.toLocaleTimeString('en-US', { 
            hour12: false, 
            minute: '2-digit', 
            second: '2-digit' 
        })
    );
    const data = systemData.metrics.cpu.map(item => item.value);
    
    systemCharts.cpu.data.labels = labels;
    systemCharts.cpu.data.datasets[0].data = data;
    systemCharts.cpu.update('none');
}

/**
 * Update Memory chart
 */
function updateMemoryChart() {
    if (!systemCharts.memory || systemData.metrics.memory.length === 0) return;
    
    const labels = systemData.metrics.memory.map(item => 
        item.timestamp.toLocaleTimeString('en-US', { 
            hour12: false, 
            minute: '2-digit', 
            second: '2-digit' 
        })
    );
    const data = systemData.metrics.memory.map(item => item.value);
    
    systemCharts.memory.data.labels = labels;
    systemCharts.memory.data.datasets[0].data = data;
    systemCharts.memory.update('none');
}

/**
 * Update Network chart
 */
function updateNetworkChart() {
    if (!systemCharts.network || systemData.metrics.network.length === 0) return;
    
    const labels = systemData.metrics.network.map(item => 
        item.timestamp.toLocaleTimeString('en-US', { 
            hour12: false, 
            minute: '2-digit', 
            second: '2-digit' 
        })
    );
    const rxData = systemData.metrics.network.map(item => item.rx);
    const txData = systemData.metrics.network.map(item => item.tx);
    
    systemCharts.network.data.labels = labels;
    systemCharts.network.data.datasets[0].data = rxData;
    systemCharts.network.data.datasets[1].data = txData;
    systemCharts.network.update('none');
}

/**
 * Update last update time display
 */
function updateLastUpdateTime() {
    const element = document.getElementById('system-last-update');
    if (element && systemData.lastUpdate) {
        element.textContent = systemData.lastUpdate.toLocaleTimeString();
    }
}

/**
 * Refresh system data manually
 */
async function refreshSystemData() {
    try {
        showLoadingSpinner(true);
        await loadSystemData();
        showToast('System data refreshed', 'success');
    } catch (error) {
        console.error('Failed to refresh system data:', error);
        showToast('Failed to refresh system data', 'error');
    } finally {
        showLoadingSpinner(false);
    }
}

/**
 * Toggle system chart visibility
 */
function toggleSystemChart(chartName) {
    const chartContainer = document.getElementById(`${chartName}-chart-container`);
    const toggleButton = document.getElementById(`toggle-${chartName}-chart`);
    
    if (chartContainer && toggleButton) {
        const isHidden = chartContainer.classList.contains('hidden');
        
        if (isHidden) {
            chartContainer.classList.remove('hidden');
            toggleButton.innerHTML = '<i class="fas fa-eye-slash mr-2"></i>Hide Chart';
        } else {
            chartContainer.classList.add('hidden');
            toggleButton.innerHTML = '<i class="fas fa-eye mr-2"></i>Show Chart';
        }
    }
}

// Format bytes helper (reuse from other modules)
function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (typeof currentTab !== 'undefined' && currentTab === 'system') {
        initSystemTab();
    }
});

// WebSocket handlers for system monitoring
if (typeof io !== 'undefined') {
    document.addEventListener('DOMContentLoaded', function() {
        if (typeof socket !== 'undefined' && socket) {
            socket.on('system_update', function(data) {
                if (currentTab === 'system') {
                    // Update system data with real-time info
                    if (data.info) systemData.info = data.info;
                    if (data.metrics) {
                        // Add new metrics to history
                        if (data.metrics.cpu) {
                            systemData.metrics.cpu.push({
                                timestamp: new Date(),
                                value: data.metrics.cpu.percent
                            });
                            if (systemData.metrics.cpu.length > 20) {
                                systemData.metrics.cpu.shift();
                            }
                        }
                        
                        if (data.metrics.memory) {
                            systemData.metrics.memory.push({
                                timestamp: new Date(),
                                value: data.metrics.memory.percent
                            });
                            if (systemData.metrics.memory.length > 20) {
                                systemData.metrics.memory.shift();
                            }
                        }
                        
                        if (data.metrics.network) {
                            systemData.metrics.network.push({
                                timestamp: new Date(),
                                rx: data.metrics.network.rx_per_sec || 0,
                                tx: data.metrics.network.tx_per_sec || 0
                            });
                            if (systemData.metrics.network.length > 20) {
                                systemData.metrics.network.shift();
                            }
                        }
                    }
                    if (data.processes) systemData.processes = data.processes;
                    
                    updateSystemDisplay();
                    updateSystemCharts();
                    systemData.lastUpdate = new Date();
                    updateLastUpdateTime();
                }
            });
        }
    });
}
