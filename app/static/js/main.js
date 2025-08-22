/**
 * Main JavaScript file for Docker Dashboard
 * Handles navigation, theme switching, and global functionality
 */

// Global variables
let currentTab = 'dashboard';
let darkMode = localStorage.getItem('darkMode') === 'true';
let socket = null;

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
    console.log('Initializing Docker Dashboard...');
    
    // Setup theme
    setupTheme();
    
    // Setup navigation
    setupNavigation();
    
    // Setup event listeners
    setupEventListeners();
    
    // Initialize WebSocket connection
    initializeWebSocket();
    
    // Load initial data
    loadInitialData();
    
    // Start periodic updates
    startPeriodicUpdates();
    
    console.log('Docker Dashboard initialized successfully');
}

/**
 * Setup theme system
 */
function setupTheme() {
    const html = document.documentElement;
    const themeToggle = document.getElementById('theme-toggle');
    
    if (darkMode) {
        html.classList.add('dark');
    } else {
        html.classList.remove('dark');
    }
    
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
}

/**
 * Toggle dark/light theme
 */
function toggleTheme() {
    darkMode = !darkMode;
    const html = document.documentElement;
    
    if (darkMode) {
        html.classList.add('dark');
    } else {
        html.classList.remove('dark');
    }
    
    localStorage.setItem('darkMode', darkMode.toString());
    showToast(darkMode ? 'Switched to dark theme' : 'Switched to light theme', 'success');
}

/**
 * Setup navigation system
 */
function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const tab = this.getAttribute('href').substring(1);
            showTab(tab);
        });
    });
}

/**
 * Show specific tab
 */
function showTab(tabName) {
    // Hide all tabs
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.add('hidden'));
    
    // Show selected tab
    const selectedTab = document.getElementById(`${tabName}-tab`);
    if (selectedTab) {
        selectedTab.classList.remove('hidden');
    }
    
    // Update navigation
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.classList.remove('active', 'px-3', 'py-2', 'rounded-md', 'text-sm', 'font-medium', 'text-blue-600', 'bg-blue-50', 'dark:bg-blue-900', 'dark:text-blue-300');
        link.classList.add('px-3', 'py-2', 'rounded-md', 'text-sm', 'font-medium', 'text-gray-500', 'hover:text-gray-700', 'hover:bg-gray-100', 'dark:text-gray-300', 'dark:hover:text-white', 'dark:hover:bg-gray-700');
    });
    
    const activeLink = document.querySelector(`a[href="#${tabName}"]`);
    if (activeLink) {
        activeLink.classList.remove('text-gray-500', 'hover:text-gray-700', 'hover:bg-gray-100', 'dark:text-gray-300', 'dark:hover:text-white', 'dark:hover:bg-gray-700');
        activeLink.classList.add('active', 'text-blue-600', 'bg-blue-50', 'dark:bg-blue-900', 'dark:text-blue-300');
    }
    
    currentTab = tabName;
    
    // Load tab-specific data
    switch(tabName) {
        case 'dashboard':
            loadDashboardData();
            break;
        case 'containers':
            if (typeof initContainersTab === 'function') {
                initContainersTab();
            } else if (typeof loadContainers === 'function') {
                loadContainers();
            }
            break;
        case 'system':
            loadSystemData();
            break;
        case 'services':
            loadServices();
            break;
        case 'logs':
            loadLogContainers();
            break;
    }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Refresh button
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            this.classList.add('animate-spin');
            refreshAllData().finally(() => {
                this.classList.remove('animate-spin');
            });
        });
    }
    
    // Global keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + R for refresh
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            refreshAllData();
        }
        
        // Tab navigation with numbers
        if ((e.ctrlKey || e.metaKey) && e.key >= '1' && e.key <= '5') {
            e.preventDefault();
            const tabs = ['dashboard', 'containers', 'system', 'services', 'logs'];
            const tabIndex = parseInt(e.key) - 1;
            if (tabs[tabIndex]) {
                showTab(tabs[tabIndex]);
            }
        }
    });
    
    // Handle window resize
    window.addEventListener('resize', handleResize);
    
    // Handle visibility change (tab focus/blur)
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            // Tab became visible, refresh data
            refreshCurrentTabData();
        }
    });
}

/**
 * Handle window resize
 */
function handleResize() {
    // Redraw charts if they exist
    if (typeof refreshCharts === 'function') {
        refreshCharts();
    }
}

/**
 * Load initial data for the application
 */
async function loadInitialData() {
    try {
        // Don't show global loading spinner - use modular loading instead
        console.log('Loading initial data...');
        
        // Load health status first (fast)
        await checkHealthStatus();
        
        // Load dashboard data progressively if it's the current tab
        if (currentTab === 'dashboard') {
            loadDashboardDataProgressively();
        }
        
    } catch (error) {
        console.error('Failed to load initial data:', error);
        showToast('Failed to load initial data', 'error');
    }
}

/**
 * Load dashboard data progressively
 */
async function loadDashboardDataProgressively() {
    // Define loading tasks in order of priority
    const loadTasks = [
        {
            componentId: 'container-stats',
            message: 'Loading container overview...',
            loadFunction: async () => {
                const data = await getContainersData();
                updateDashboardContainerStats(data.data);
                return data;
            },
            errorMessage: 'Failed to load container overview',
            delay: 100
        },
        {
            componentId: 'running-containers',
            message: 'Loading running containers...',
            loadFunction: async () => {
                const data = await getContainersData();
                updateRunningContainersList(data.data.containers);
                return data;
            },
            errorMessage: 'Failed to load running containers',
            delay: 100
        },
        {
            componentId: 'system-info',
            message: 'Loading system information...',
            loadFunction: async () => {
                const data = await getSystemData();
                updateSystemQuickStats(data.data);
                return data;
            },
            errorMessage: 'Failed to load system information',
            delay: 100
        }
    ];
    
    // Load progressively
    await loadingManager.loadProgressively(loadTasks);
}

/**
 * Update dashboard container stats
 */
function updateDashboardContainerStats(data) {
    const containerCount = document.getElementById('container-count');
    const runningCount = document.getElementById('running-count');
    
    if (containerCount) {
        containerCount.textContent = data.total.toString();
        containerCount.classList.add('animate-pulse-slow');
        setTimeout(() => containerCount.classList.remove('animate-pulse-slow'), 1000);
    }
    
    if (runningCount) {
        runningCount.textContent = data.running.toString();
        runningCount.classList.add('animate-pulse-slow');
        setTimeout(() => runningCount.classList.remove('animate-pulse-slow'), 1000);
    }
}

/**
 * Update running containers list
 */
function updateRunningContainersList(containers) {
    const runningContainersElement = document.getElementById('running-containers');
    if (!runningContainersElement) return;
    
    const runningContainers = containers.filter(c => c.is_running);
    
    if (runningContainers.length === 0) {
        loadingManager.showEmpty('running-containers', 'No containers running', 'fa-box');
        return;
    }
    
    const html = runningContainers.slice(0, 5).map(container => `
        <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div class="flex items-center">
                <div class="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
                <div>
                    <p class="font-medium text-gray-900 dark:text-white">${container.name}</p>
                    <p class="text-sm text-gray-500 dark:text-gray-400">${container.image.split(':')[0]}</p>
                </div>
            </div>
            <div class="text-right">
                <p class="text-xs text-gray-500 dark:text-gray-400">Running</p>
                ${container.ports && container.ports.length > 0 ? 
                    `<p class="text-xs text-blue-600 dark:text-blue-400">${container.ports[0]}</p>` : 
                    ''
                }
            </div>
        </div>
    `).join('');
    
    runningContainersElement.innerHTML = html;
}

/**
 * Update system quick stats
 */
function updateSystemQuickStats(systemData) {
    if (!systemData) {
        // Show placeholder values
        updateQuickStatElement('cpu-usage', 'cpu-progress', '-', 0);
        updateQuickStatElement('memory-usage', 'memory-progress', '-', 0);
        updateQuickStatElement('disk-usage', 'disk-progress', '-', 0);
        return;
    }
    
    // CPU Usage
    const cpuPercent = systemData.cpu?.percent || 0;
    updateQuickStatElement('cpu-usage', 'cpu-progress', `${cpuPercent.toFixed(1)}%`, cpuPercent, getCpuColorClass(cpuPercent));
    
    // Memory Usage
    const memoryPercent = systemData.memory?.percent || 0;
    updateQuickStatElement('memory-usage', 'memory-progress', `${memoryPercent.toFixed(1)}%`, memoryPercent, getMemoryColorClass(memoryPercent));
    
    // Disk Usage
    const diskPercent = systemData.summary?.disk_usage_percent || 0;
    updateQuickStatElement('disk-usage', 'disk-progress', `${diskPercent.toFixed(1)}%`, diskPercent, getDiskColorClass(diskPercent));
}

/**
 * Update a quick stat element
 */
function updateQuickStatElement(usageId, progressId, text, percent, colorClass = 'bg-blue-600') {
    const usageElement = document.getElementById(usageId);
    const progressElement = document.getElementById(progressId);
    
    if (usageElement) {
        usageElement.textContent = text;
        usageElement.classList.add('animate-pulse-slow');
        setTimeout(() => usageElement.classList.remove('animate-pulse-slow'), 1000);
    }
    
    if (progressElement) {
        progressElement.style.width = `${Math.min(percent, 100)}%`;
        progressElement.className = `h-2 rounded-full transition-all duration-300 ${colorClass}`;
    }
}

// Utility functions for progress bar colors
function getCpuColorClass(percent) {
    if (percent > 80) return 'bg-red-600';
    if (percent > 60) return 'bg-orange-600';
    if (percent > 40) return 'bg-yellow-600';
    return 'bg-green-600';
}

function getMemoryColorClass(percent) {
    if (percent > 85) return 'bg-red-600';
    if (percent > 70) return 'bg-orange-600';
    if (percent > 50) return 'bg-yellow-600';
    return 'bg-purple-600';
}

function getDiskColorClass(percent) {
    if (percent > 90) return 'bg-red-600';
    if (percent > 80) return 'bg-orange-600';
    if (percent > 60) return 'bg-yellow-600';
    return 'bg-blue-600';
}

/**
 * Check health status of all services
 */
async function checkHealthStatus() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        
        updateStatusIndicators(data.services);
        
        if (data.status === 'healthy') {
            console.log('All services healthy');
        } else {
            console.warn('Some services are unhealthy:', data.services);
        }
        
    } catch (error) {
        console.error('Health check failed:', error);
        updateStatusIndicators({
            ssh: { healthy: false },
            docker: { healthy: false },
            monitoring: { healthy: false }
        });
    }
}

/**
 * Update status indicators in the navigation
 */
function updateStatusIndicators(services) {
    const sshStatus = document.getElementById('ssh-status');
    const dockerStatus = document.getElementById('docker-status');
    const glancesStatus = document.getElementById('glances-status');
    
    if (sshStatus) {
        const dot = sshStatus.querySelector('.w-2');
        if (services.ssh?.healthy) {
            dot.classList.remove('bg-gray-400', 'bg-red-500');
            dot.classList.add('bg-green-500');
        } else {
            dot.classList.remove('bg-gray-400', 'bg-green-500');
            dot.classList.add('bg-red-500');
        }
    }
    
    if (dockerStatus) {
        const dot = dockerStatus.querySelector('.w-2');
        if (services.docker?.healthy) {
            dot.classList.remove('bg-gray-400', 'bg-red-500');
            dot.classList.add('bg-green-500');
        } else {
            dot.classList.remove('bg-gray-400', 'bg-green-500');
            dot.classList.add('bg-red-500');
        }
    }
    
    if (glancesStatus) {
        const dot = glancesStatus.querySelector('.w-2');
        if (services.monitoring?.healthy) {
            dot.classList.remove('bg-gray-400', 'bg-red-500');
            dot.classList.add('bg-green-500');
        } else {
            dot.classList.remove('bg-gray-400', 'bg-green-500');
            dot.classList.add('bg-red-500');
        }
    }
}

/**
 * Refresh all data
 */
async function refreshAllData() {
    try {
        showLoadingSpinner(true);
        
        // Check health status
        await checkHealthStatus();
        
        // Refresh current tab data
        await refreshCurrentTabData();
        
        showToast('Data refreshed successfully', 'success');
        
    } catch (error) {
        console.error('Failed to refresh data:', error);
        showToast('Failed to refresh data', 'error');
    } finally {
        showLoadingSpinner(false);
    }
}

/**
 * Refresh data for current tab
 */
async function refreshCurrentTabData() {
    switch(currentTab) {
        case 'dashboard':
            await loadDashboardData();
            break;
        case 'containers':
            await loadContainers();
            break;
        case 'system':
            await loadSystemData();
            break;
        case 'services':
            await loadServices();
            break;
        case 'logs':
            await refreshLogs();
            break;
    }
}

/**
 * Start periodic updates
 */
function startPeriodicUpdates() {
    // Update every 30 seconds
    setInterval(async () => {
        if (!document.hidden) {
            await checkHealthStatus();
            
            // Update dashboard if it's the current tab
            if (currentTab === 'dashboard') {
                await loadDashboardData();
            }
        }
    }, 30000);
}

/**
 * Show/hide loading spinner
 */
function showLoadingSpinner(show) {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) {
        if (show) {
            spinner.classList.remove('hidden');
        } else {
            spinner.classList.add('hidden');
        }
    }
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `flex items-center p-4 mb-4 text-sm rounded-lg shadow-lg transition-all duration-300 ${getToastClasses(type)}`;
    
    const icon = getToastIcon(type);
    toast.innerHTML = `
        <div class="inline-flex items-center justify-center flex-shrink-0 w-8 h-8 rounded-lg mr-3">
            <i class="fas ${icon}"></i>
        </div>
        <div class="ml-3 text-sm font-normal">${message}</div>
        <button type="button" class="ml-auto -mx-1.5 -my-1.5 rounded-lg p-1.5 inline-flex h-8 w-8 hover:bg-gray-100 dark:hover:bg-gray-700" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    // Auto-remove after duration
    setTimeout(() => {
        if (toast.parentNode) {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }
    }, duration);
}

/**
 * Get toast classes based on type
 */
function getToastClasses(type) {
    const classes = {
        success: 'text-green-800 bg-green-50 dark:bg-green-800 dark:text-green-200',
        error: 'text-red-800 bg-red-50 dark:bg-red-800 dark:text-red-200',
        warning: 'text-orange-800 bg-orange-50 dark:bg-orange-800 dark:text-orange-200',
        info: 'text-blue-800 bg-blue-50 dark:bg-blue-800 dark:text-blue-200'
    };
    return classes[type] || classes.info;
}

/**
 * Get toast icon based on type
 */
function getToastIcon(type) {
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-times-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    return icons[type] || icons.info;
}

/**
 * Format bytes to human readable format
 */
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Format duration from seconds to human readable format
 */
function formatDuration(seconds) {
    if (seconds < 60) {
        return `${seconds}s`;
    } else if (seconds < 3600) {
        return `${Math.floor(seconds / 60)}m`;
    } else if (seconds < 86400) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    } else {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        return `${days}d ${hours}h`;
    }
}

/**
 * Make HTTP request with error handling
 */
async function makeRequest(url, options = {}) {
    try {
        const response = await fetch(url, options);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Request failed');
        }
        
        return data;
    } catch (error) {
        console.error(`Request failed for ${url}:`, error);
        throw error;
    }
}

/**
 * Initialize WebSocket connection
 */
function initializeWebSocket() {
    if (typeof io !== 'undefined') {
        socket = io();
        
        socket.on('connect', function() {
            console.log('WebSocket connected');
        });
        
        socket.on('disconnect', function() {
            console.log('WebSocket disconnected');
        });
        
        socket.on('error', function(data) {
            console.error('WebSocket error:', data);
            showToast(data.message || 'Connection error', 'error');
        });
    } else {
        console.warn('Socket.IO not available, falling back to polling');
    }
}

// Export functions for use in other modules
window.dashboardApp = {
    showTab,
    showToast,
    makeRequest,
    formatBytes,
    formatDuration,
    refreshAllData,
    socket
};
