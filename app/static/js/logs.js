/**
 * Logs tab functionality
 * Handles container logs viewing and management
 */

let logsData = {
    containers: [],
    currentContainer: null,
    logs: [],
    isStreaming: false,
    maxLines: 1000,
    searchQuery: '',
    logLevel: 'all',
    autoScroll: true
};

/**
 * Initialize logs tab
 */
function initLogsTab() {
    loadContainersForLogs();
    setupLogControls();
    setupLogSearch();
}

/**
 * Load containers for log selection
 */
async function loadContainersForLogs() {
    try {
        const data = await makeRequest('/api/containers/');
        logsData.containers = (data.data || []).filter(c => c.is_running);
        
        populateContainerSelector();
        
        // Auto-select first running container if none selected
        if (!logsData.currentContainer && logsData.containers.length > 0) {
            setLogContainer(logsData.containers[0].id);
        }
        
    } catch (error) {
        console.error('Failed to load containers for logs:', error);
        logsData.containers = [];
        populateContainerSelector();
    }
}

/**
 * Populate container selector dropdown
 */
function populateContainerSelector() {
    const selector = document.getElementById('log-container-selector');
    if (!selector) return;
    
    if (logsData.containers.length === 0) {
        selector.innerHTML = '<option value="">No running containers available</option>';
        return;
    }
    
    const options = logsData.containers.map(container => 
        `<option value="${container.id}" ${container.id === logsData.currentContainer ? 'selected' : ''}>
            ${container.name}
        </option>`
    ).join('');
    
    selector.innerHTML = `
        <option value="">Select a container...</option>
        ${options}
    `;
}

/**
 * Set container for log viewing
 */
function setLogContainer(containerId) {
    logsData.currentContainer = containerId;
    
    const selector = document.getElementById('log-container-selector');
    if (selector) {
        selector.value = containerId;
    }
    
    clearLogs();
    loadContainerLogs();
}

/**
 * Setup log controls
 */
function setupLogControls() {
    const containerSelector = document.getElementById('log-container-selector');
    const maxLinesInput = document.getElementById('log-max-lines');
    const logLevelSelect = document.getElementById('log-level-filter');
    const autoScrollToggle = document.getElementById('log-auto-scroll');
    
    if (containerSelector) {
        containerSelector.addEventListener('change', function() {
            if (this.value) {
                setLogContainer(this.value);
            } else {
                logsData.currentContainer = null;
                clearLogs();
            }
        });
    }
    
    if (maxLinesInput) {
        maxLinesInput.addEventListener('change', function() {
            const value = parseInt(this.value);
            if (value > 0 && value <= 10000) {
                logsData.maxLines = value;
                loadContainerLogs();
            }
        });
    }
    
    if (logLevelSelect) {
        logLevelSelect.addEventListener('change', function() {
            logsData.logLevel = this.value;
            filterAndDisplayLogs();
        });
    }
    
    if (autoScrollToggle) {
        autoScrollToggle.addEventListener('change', function() {
            logsData.autoScroll = this.checked;
        });
    }
}

/**
 * Setup log search
 */
function setupLogSearch() {
    const searchInput = document.getElementById('log-search');
    
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                logsData.searchQuery = this.value.trim().toLowerCase();
                filterAndDisplayLogs();
            }, 300);
        });
    }
}

/**
 * Load container logs
 */
async function loadContainerLogs() {
    if (!logsData.currentContainer) return;
    
    try {
        showLoadingState('logs-container', true);
        
        const data = await makeRequest(
            `/api/containers/${logsData.currentContainer}/logs?lines=${logsData.maxLines}`,
            { method: 'GET' }
        );
        
        logsData.logs = data.data || [];
        filterAndDisplayLogs();
        
    } catch (error) {
        console.error('Failed to load container logs:', error);
        showToast('Failed to load container logs', 'error');
        displayEmptyLogs('Failed to load logs');
    }
}

/**
 * Filter and display logs
 */
function filterAndDisplayLogs() {
    let filteredLogs = [...logsData.logs];
    
    // Apply search filter
    if (logsData.searchQuery) {
        filteredLogs = filteredLogs.filter(log => 
            log.toLowerCase().includes(logsData.searchQuery)
        );
    }
    
    // Apply log level filter
    if (logsData.logLevel !== 'all') {
        filteredLogs = filteredLogs.filter(log => {
            const logLower = log.toLowerCase();
            switch (logsData.logLevel) {
                case 'error': return logLower.includes('error') || logLower.includes('err');
                case 'warning': return logLower.includes('warn') || logLower.includes('warning');
                case 'info': return logLower.includes('info');
                case 'debug': return logLower.includes('debug');
                default: return true;
            }
        });
    }
    
    displayLogs(filteredLogs);
}

/**
 * Display logs in the container
 */
function displayLogs(logs) {
    const container = document.getElementById('logs-container');
    if (!container) return;
    
    showLoadingState('logs-container', false);
    
    if (logs.length === 0) {
        displayEmptyLogs('No logs found matching your criteria');
        return;
    }
    
    const logsHTML = logs.map((log, index) => {
        const timestamp = extractTimestamp(log);
        const level = detectLogLevel(log);
        const content = formatLogContent(log);
        
        return `
            <div class="log-entry flex text-sm font-mono border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors" data-index="${index}">
                <div class="flex-shrink-0 w-20 p-2 text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 border-r border-gray-200 dark:border-gray-600">
                    ${index + 1}
                </div>
                ${timestamp ? `
                    <div class="flex-shrink-0 w-32 p-2 text-xs text-gray-600 dark:text-gray-300 bg-gray-50 dark:bg-gray-800 border-r border-gray-200 dark:border-gray-600">
                        ${timestamp}
                    </div>
                ` : ''}
                <div class="flex-shrink-0 w-16 p-2 text-center">
                    <span class="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${getLogLevelClass(level)}">
                        ${level.toUpperCase()}
                    </span>
                </div>
                <div class="flex-1 p-2 text-gray-900 dark:text-gray-100 whitespace-pre-wrap break-all">
                    ${content}
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = `
        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
            <div class="max-h-96 overflow-y-auto">
                ${logsHTML}
            </div>
        </div>
    `;
    
    updateLogStats(logs.length);
    
    // Auto-scroll to bottom if enabled
    if (logsData.autoScroll) {
        scrollLogsToBottom();
    }
}

/**
 * Display empty logs state
 */
function displayEmptyLogs(message = 'No logs available') {
    const container = document.getElementById('logs-container');
    if (!container) return;
    
    container.innerHTML = `
        <div class="text-center py-12 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg">
            <i class="fas fa-file-alt text-6xl text-gray-300 dark:text-gray-600 mb-4"></i>
            <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">${message}</h3>
            <p class="text-gray-500 dark:text-gray-400 mb-6">
                ${logsData.currentContainer ? 'Try adjusting your search or filter criteria.' : 'Select a container to view logs.'}
            </p>
            ${logsData.currentContainer ? `
                <button onclick="loadContainerLogs()" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                    <i class="fas fa-refresh mr-2"></i>Refresh Logs
                </button>
            ` : ''}
        </div>
    `;
}

/**
 * Extract timestamp from log entry
 */
function extractTimestamp(log) {
    const timestampRegex = /^(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d{3})?(?:Z|[+-]\d{2}:\d{2})?)/;
    const match = log.match(timestampRegex);
    return match ? new Date(match[1]).toLocaleTimeString() : null;
}

/**
 * Detect log level from log entry
 */
function detectLogLevel(log) {
    const logLower = log.toLowerCase();
    
    if (logLower.includes('error') || logLower.includes('err') || logLower.includes('fatal')) return 'error';
    if (logLower.includes('warn') || logLower.includes('warning')) return 'warning';
    if (logLower.includes('info') || logLower.includes('information')) return 'info';
    if (logLower.includes('debug') || logLower.includes('trace')) return 'debug';
    
    return 'info';
}

/**
 * Format log content for display
 */
function formatLogContent(log) {
    // Remove timestamp if present
    const timestampRegex = /^(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d{3})?(?:Z|[+-]\d{2}:\d{2})?)/;
    let content = log.replace(timestampRegex, '').trim();
    
    // Escape HTML
    content = content
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#x27;');
    
    // Highlight search terms
    if (logsData.searchQuery) {
        const regex = new RegExp(`(${escapeRegExp(logsData.searchQuery)})`, 'gi');
        content = content.replace(regex, '<mark class="bg-yellow-200 dark:bg-yellow-800">$1</mark>');
    }
    
    return content;
}

/**
 * Get CSS class for log level
 */
function getLogLevelClass(level) {
    const classes = {
        error: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
        warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
        info: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
        debug: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300'
    };
    
    return classes[level] || classes.info;
}

/**
 * Update log statistics
 */
function updateLogStats(filteredCount) {
    const totalElement = document.getElementById('logs-total-count');
    const filteredElement = document.getElementById('logs-filtered-count');
    
    if (totalElement) {
        totalElement.textContent = logsData.logs.length;
    }
    
    if (filteredElement) {
        filteredElement.textContent = filteredCount;
    }
}

/**
 * Scroll logs to bottom
 */
function scrollLogsToBottom() {
    const container = document.querySelector('#logs-container .overflow-y-auto');
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}

/**
 * Clear logs display
 */
function clearLogs() {
    logsData.logs = [];
    displayEmptyLogs();
}

/**
 * Download logs as file
 */
function downloadLogs() {
    if (!logsData.currentContainer || logsData.logs.length === 0) {
        showToast('No logs available to download', 'warning');
        return;
    }
    
    const container = logsData.containers.find(c => c.id === logsData.currentContainer);
    const filename = `${container ? container.name : 'container'}_logs_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
    
    const content = logsData.logs.join('\n');
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showToast('Logs downloaded successfully', 'success');
}

/**
 * Clear log search and filters
 */
function clearLogFilters() {
    logsData.searchQuery = '';
    logsData.logLevel = 'all';
    
    const searchInput = document.getElementById('log-search');
    const logLevelSelect = document.getElementById('log-level-filter');
    
    if (searchInput) searchInput.value = '';
    if (logLevelSelect) logLevelSelect.value = 'all';
    
    filterAndDisplayLogs();
}

/**
 * Toggle log streaming (if supported)
 */
function toggleLogStreaming() {
    logsData.isStreaming = !logsData.isStreaming;
    
    const button = document.getElementById('toggle-log-streaming');
    if (button) {
        if (logsData.isStreaming) {
            button.innerHTML = '<i class="fas fa-stop mr-2"></i>Stop Streaming';
            button.className = 'px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors';
            startLogStreaming();
        } else {
            button.innerHTML = '<i class="fas fa-play mr-2"></i>Start Streaming';
            button.className = 'px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors';
            stopLogStreaming();
        }
    }
}

/**
 * Start log streaming (mock implementation)
 */
function startLogStreaming() {
    // This would be implemented with WebSocket or Server-Sent Events
    showToast('Log streaming started', 'info');
}

/**
 * Stop log streaming
 */
function stopLogStreaming() {
    showToast('Log streaming stopped', 'info');
}

/**
 * Escape regex special characters
 */
function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Refresh logs manually
 */
async function refreshLogs() {
    if (!logsData.currentContainer) {
        showToast('No container selected', 'warning');
        return;
    }
    
    try {
        showLoadingSpinner(true);
        await loadContainerLogs();
        showToast('Logs refreshed', 'success');
    } catch (error) {
        console.error('Failed to refresh logs:', error);
        showToast('Failed to refresh logs', 'error');
    } finally {
        showLoadingSpinner(false);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (typeof currentTab !== 'undefined' && currentTab === 'logs') {
        initLogsTab();
    }
});

// WebSocket handlers for logs
if (typeof io !== 'undefined') {
    document.addEventListener('DOMContentLoaded', function() {
        if (typeof socket !== 'undefined' && socket) {
            socket.on('container_logs_update', function(data) {
                if (currentTab === 'logs' && data.container_id === logsData.currentContainer) {
                    // Append new log entries if streaming
                    if (logsData.isStreaming && data.logs) {
                        logsData.logs.push(...data.logs);
                        
                        // Keep only the last maxLines entries
                        if (logsData.logs.length > logsData.maxLines) {
                            logsData.logs = logsData.logs.slice(-logsData.maxLines);
                        }
                        
                        filterAndDisplayLogs();
                    }
                }
            });
        }
    });
}
