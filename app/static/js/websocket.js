/**
 * WebSocket functionality
 * Handles real-time communication with the server
 */

let socket = null;
let socketStatus = 'disconnected';
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;
let reconnectTimeout = null;

/**
 * Initialize WebSocket connection
 */
function initWebSocket() {
    // Check if Socket.IO is available
    if (typeof io === 'undefined') {
        console.warn('Socket.IO not available, real-time updates disabled');
        updateSocketStatus('unavailable');
        return;
    }
    
    try {
        socket = io({
            transports: ['websocket', 'polling'],
            upgrade: true,
            timeout: 20000,
            forceNew: false
        });
        
        setupSocketEventHandlers();
        
    } catch (error) {
        console.error('Failed to initialize WebSocket:', error);
        updateSocketStatus('error');
    }
}

/**
 * Setup WebSocket event handlers
 */
function setupSocketEventHandlers() {
    if (!socket) return;
    
    // Connection events
    socket.on('connect', function() {
        console.log('WebSocket connected');
        updateSocketStatus('connected');
        reconnectAttempts = 0;
        clearTimeout(reconnectTimeout);
        
        showToast('Real-time updates enabled', 'success');
        
        // Request initial data
        requestInitialData();
    });
    
    socket.on('disconnect', function(reason) {
        console.log('WebSocket disconnected:', reason);
        updateSocketStatus('disconnected');
        
        if (reason === 'io server disconnect') {
            // Server initiated disconnect, don't reconnect
            showToast('Server disconnected', 'warning');
        } else {
            // Client-side disconnect, attempt to reconnect
            showToast('Connection lost, attempting to reconnect...', 'warning');
            attemptReconnect();
        }
    });
    
    socket.on('connect_error', function(error) {
        console.error('WebSocket connection error:', error);
        updateSocketStatus('error');
        
        showToast('Connection error', 'error');
        attemptReconnect();
    });
    
    socket.on('reconnect', function(attemptNumber) {
        console.log('WebSocket reconnected after', attemptNumber, 'attempts');
        updateSocketStatus('connected');
        showToast('Reconnected successfully', 'success');
        
        requestInitialData();
    });
    
    socket.on('reconnect_error', function(error) {
        console.error('WebSocket reconnection error:', error);
        updateSocketStatus('error');
    });
    
    socket.on('reconnect_failed', function() {
        console.error('WebSocket reconnection failed');
        updateSocketStatus('failed');
        showToast('Failed to reconnect. Please refresh the page.', 'error');
    });
    
    // Data update events
    setupDataEventHandlers();
}

/**
 * Setup data event handlers
 */
function setupDataEventHandlers() {
    if (!socket) return;
    
    // Container updates
    socket.on('container_update', function(data) {
        console.log('Container update received:', data);
        
        // Broadcast to all tabs that might need this data
        if (typeof handleContainerUpdate === 'function') {
            handleContainerUpdate(data);
        }
        
        // Update specific tab content if active
        switch (currentTab) {
            case 'dashboard':
                if (typeof dashboardData !== 'undefined') {
                    dashboardData.containers = data.containers || [];
                    if (typeof updateDashboardStats === 'function') updateDashboardStats();
                    if (typeof updateRunningContainers === 'function') updateRunningContainers();
                }
                break;
                
            case 'containers':
                if (typeof containersData !== 'undefined') {
                    containersData.containers = data.containers || [];
                    if (typeof applyFiltersAndSort === 'function') applyFiltersAndSort();
                    if (typeof renderContainers === 'function') renderContainers();
                    if (typeof updateContainerCounts === 'function') updateContainerCounts();
                }
                break;
                
            case 'services':
                if (typeof servicesData !== 'undefined') {
                    servicesData.allContainers = data.containers || [];
                    if (typeof mapServicesToContainers === 'function') mapServicesToContainers();
                    if (typeof renderServices === 'function') renderServices();
                    if (typeof updateServicesStats === 'function') updateServicesStats();
                }
                break;
        }
    });
    
    // System updates
    socket.on('system_update', function(data) {
        console.log('System update received:', data);
        
        // Broadcast to all tabs that might need this data
        if (typeof handleSystemUpdate === 'function') {
            handleSystemUpdate(data);
        }
        
        // Update specific tab content if active
        switch (currentTab) {
            case 'dashboard':
                if (typeof dashboardData !== 'undefined') {
                    dashboardData.systemInfo = data;
                    if (typeof updateSystemInfo === 'function') updateSystemInfo();
                    if (typeof updateQuickStats === 'function') updateQuickStats();
                }
                break;
                
            case 'system':
                if (typeof systemData !== 'undefined') {
                    if (data.info) systemData.info = data.info;
                    if (data.metrics) {
                        addMetricsToHistory(data.metrics);
                    }
                    if (data.processes) systemData.processes = data.processes;
                    
                    if (typeof updateSystemDisplay === 'function') updateSystemDisplay();
                    if (typeof updateSystemCharts === 'function') updateSystemCharts();
                }
                break;
        }
    });
    
    // Log updates
    socket.on('container_logs_update', function(data) {
        console.log('Container logs update received for:', data.container_id);
        
        if (currentTab === 'logs' && typeof logsData !== 'undefined') {
            if (data.container_id === logsData.currentContainer && logsData.isStreaming) {
                if (data.logs && Array.isArray(data.logs)) {
                    logsData.logs.push(...data.logs);
                    
                    // Keep only the last maxLines entries
                    if (logsData.logs.length > logsData.maxLines) {
                        logsData.logs = logsData.logs.slice(-logsData.maxLines);
                    }
                    
                    if (typeof filterAndDisplayLogs === 'function') {
                        filterAndDisplayLogs();
                    }
                }
            }
        }
    });
    
    // Error events
    socket.on('error', function(error) {
        console.error('WebSocket error:', error);
        showToast('WebSocket error: ' + error.message, 'error');
    });
    
    // Custom application events
    socket.on('notification', function(data) {
        if (data.type && data.message) {
            showToast(data.message, data.type);
        }
    });
}

/**
 * Add metrics to history for charts
 */
function addMetricsToHistory(metrics) {
    if (typeof systemData === 'undefined') return;
    
    const timestamp = new Date();
    
    if (metrics.cpu) {
        systemData.metrics.cpu.push({
            timestamp: timestamp,
            value: metrics.cpu.percent
        });
        if (systemData.metrics.cpu.length > 20) {
            systemData.metrics.cpu.shift();
        }
    }
    
    if (metrics.memory) {
        systemData.metrics.memory.push({
            timestamp: timestamp,
            value: metrics.memory.percent
        });
        if (systemData.metrics.memory.length > 20) {
            systemData.metrics.memory.shift();
        }
    }
    
    if (metrics.network) {
        systemData.metrics.network.push({
            timestamp: timestamp,
            rx: metrics.network.rx_per_sec || 0,
            tx: metrics.network.tx_per_sec || 0
        });
        if (systemData.metrics.network.length > 20) {
            systemData.metrics.network.shift();
        }
    }
}

/**
 * Request initial data from server
 */
function requestInitialData() {
    if (!socket || socketStatus !== 'connected') return;
    
    // Request data based on current tab
    switch (currentTab) {
        case 'dashboard':
        case 'containers':
        case 'services':
            socket.emit('request_containers');
            break;
            
        case 'system':
            socket.emit('request_system_info');
            socket.emit('request_system_metrics');
            break;
            
        case 'logs':
            if (typeof logsData !== 'undefined' && logsData.currentContainer) {
                socket.emit('request_container_logs', {
                    container_id: logsData.currentContainer,
                    lines: logsData.maxLines
                });
            }
            break;
    }
}

/**
 * Attempt to reconnect WebSocket
 */
function attemptReconnect() {
    if (reconnectAttempts >= maxReconnectAttempts) {
        console.error('Max reconnection attempts reached');
        updateSocketStatus('failed');
        return;
    }
    
    reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts - 1), 30000); // Exponential backoff, max 30s
    
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${reconnectAttempts}/${maxReconnectAttempts})`);
    
    reconnectTimeout = setTimeout(() => {
        if (socket && socketStatus !== 'connected') {
            socket.connect();
        }
    }, delay);
}

/**
 * Update socket status display
 */
function updateSocketStatus(status) {
    socketStatus = status;
    
    const indicator = document.getElementById('websocket-status');
    if (!indicator) return;
    
    const statusConfig = {
        connected: {
            icon: 'wifi',
            color: 'text-green-600',
            title: 'Real-time updates enabled'
        },
        disconnected: {
            icon: 'wifi',
            color: 'text-yellow-600',
            title: 'Disconnected - attempting to reconnect'
        },
        error: {
            icon: 'exclamation-triangle',
            color: 'text-red-600',
            title: 'Connection error'
        },
        failed: {
            icon: 'times-circle',
            color: 'text-red-600',
            title: 'Connection failed'
        },
        unavailable: {
            icon: 'info-circle',
            color: 'text-gray-600',
            title: 'Real-time updates unavailable'
        }
    };
    
    const config = statusConfig[status] || statusConfig.disconnected;
    
    indicator.innerHTML = `
        <i class="fas fa-${config.icon} ${config.color}" title="${config.title}"></i>
    `;
}

/**
 * Subscribe to container updates for specific container
 */
function subscribeToContainerUpdates(containerId) {
    if (socket && socketStatus === 'connected') {
        socket.emit('subscribe_container', { container_id: containerId });
    }
}

/**
 * Unsubscribe from container updates for specific container
 */
function unsubscribeFromContainerUpdates(containerId) {
    if (socket && socketStatus === 'connected') {
        socket.emit('unsubscribe_container', { container_id: containerId });
    }
}

/**
 * Subscribe to system monitoring updates
 */
function subscribeToSystemUpdates() {
    if (socket && socketStatus === 'connected') {
        socket.emit('subscribe_system');
    }
}

/**
 * Unsubscribe from system monitoring updates
 */
function unsubscribeFromSystemUpdates() {
    if (socket && socketStatus === 'connected') {
        socket.emit('unsubscribe_system');
    }
}

/**
 * Subscribe to log updates for specific container
 */
function subscribeToLogUpdates(containerId) {
    if (socket && socketStatus === 'connected') {
        socket.emit('subscribe_logs', { container_id: containerId });
    }
}

/**
 * Unsubscribe from log updates for specific container
 */
function unsubscribeFromLogUpdates(containerId) {
    if (socket && socketStatus === 'connected') {
        socket.emit('unsubscribe_logs', { container_id: containerId });
    }
}

/**
 * Send container action via WebSocket
 */
function sendContainerAction(containerId, action) {
    if (socket && socketStatus === 'connected') {
        socket.emit('container_action', {
            container_id: containerId,
            action: action
        });
        return true;
    }
    return false;
}

/**
 * Manual connection management
 */
function connectWebSocket() {
    if (socket && socketStatus !== 'connected') {
        socket.connect();
    } else if (!socket) {
        initWebSocket();
    }
}

function disconnectWebSocket() {
    if (socket) {
        socket.disconnect();
        updateSocketStatus('disconnected');
    }
}

/**
 * Get WebSocket status
 */
function getSocketStatus() {
    return {
        status: socketStatus,
        connected: socketStatus === 'connected',
        reconnectAttempts: reconnectAttempts
    };
}

/**
 * Handle tab change for WebSocket subscriptions
 */
function handleTabChangeForWebSocket(newTab) {
    if (socket && socketStatus === 'connected') {
        // Unsubscribe from previous tab's updates
        switch (previousTab) {
            case 'system':
                unsubscribeFromSystemUpdates();
                break;
        }
        
        // Subscribe to new tab's updates
        switch (newTab) {
            case 'system':
                subscribeToSystemUpdates();
                break;
        }
        
        // Request initial data for new tab
        setTimeout(() => requestInitialData(), 100);
    }
}

// Initialize WebSocket when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Add a small delay to ensure other scripts are loaded
    setTimeout(initWebSocket, 500);
});

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Page is hidden, reduce update frequency or disconnect
        if (socket && socketStatus === 'connected') {
            // Could emit a 'page_hidden' event to server
            socket.emit('page_visibility', { visible: false });
        }
    } else {
        // Page is visible, resume normal operation
        if (socket && socketStatus === 'connected') {
            socket.emit('page_visibility', { visible: true });
            requestInitialData();
        } else if (socketStatus === 'disconnected') {
            // Try to reconnect if disconnected
            connectWebSocket();
        }
    }
});

// Handle page unload
window.addEventListener('beforeunload', function() {
    if (socket) {
        socket.disconnect();
    }
});

// Export functions for global access
window.socketManager = {
    connect: connectWebSocket,
    disconnect: disconnectWebSocket,
    getStatus: getSocketStatus,
    subscribeToContainerUpdates,
    unsubscribeFromContainerUpdates,
    subscribeToSystemUpdates,
    unsubscribeFromSystemUpdates,
    subscribeToLogUpdates,
    unsubscribeFromLogUpdates,
    sendContainerAction
};
