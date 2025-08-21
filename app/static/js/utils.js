/**
 * Utility functions for Docker Dashboard
 */

/**
 * Format bytes to human readable format
 * @param {number} bytes 
 * @param {number} decimals 
 * @returns {string}
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
 * Format uptime to human readable format
 * @param {number} seconds 
 * @returns {string}
 */
function formatUptime(seconds) {
    if (!seconds) return 'Unknown';

    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) {
        return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}

/**
 * Format date to relative time
 * @param {string|Date} date 
 * @returns {string}
 */
function formatRelativeTime(date) {
    const now = new Date();
    const target = new Date(date);
    const diffMs = now - target;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSecs < 60) {
        return 'just now';
    } else if (diffMins < 60) {
        return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
        return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else if (diffDays < 30) {
        return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    } else {
        return target.toLocaleDateString();
    }
}

/**
 * Debounce function calls
 * @param {Function} func 
 * @param {number} wait 
 * @param {boolean} immediate 
 * @returns {Function}
 */
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

/**
 * Throttle function calls
 * @param {Function} func 
 * @param {number} limit 
 * @returns {Function}
 */
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Show toast notification
 * @param {string} message 
 * @param {string} type 
 * @param {number} duration 
 */
function showToast(message, type = 'info', duration = 3000) {
    // Remove existing toasts
    const existingToasts = document.querySelectorAll('.toast');
    existingToasts.forEach(toast => toast.remove());

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas fa-${getToastIcon(type)}"></i>
            <span>${message}</span>
            <button class="toast-close" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;

    // Toast styles
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        padding: 1rem;
        border-radius: 4px;
        color: white;
        min-width: 300px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        animation: slideInRight 0.3s ease-out;
        background-color: ${getToastColor(type)};
    `;

    document.body.appendChild(toast);

    // Auto remove
    if (duration > 0) {
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, duration);
    }
}

/**
 * Get toast icon based on type
 * @param {string} type 
 * @returns {string}
 */
function getToastIcon(type) {
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    return icons[type] || 'info-circle';
}

/**
 * Get toast color based on type
 * @param {string} type 
 * @returns {string}
 */
function getToastColor(type) {
    const colors = {
        success: '#28a745',
        error: '#dc3545',
        warning: '#ffc107',
        info: '#17a2b8'
    };
    return colors[type] || '#17a2b8';
}

/**
 * Show loading overlay
 * @param {string} message 
 */
function showLoading(message = 'Loading...') {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.querySelector('span').textContent = message;
        overlay.style.display = 'flex';
    }
}

/**
 * Hide loading overlay
 */
function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

/**
 * Confirm action with user
 * @param {string} message 
 * @param {string} title 
 * @returns {Promise<boolean>}
 */
async function confirmAction(message, title = 'Confirm Action') {
    return new Promise((resolve) => {
        const modal = document.createElement('div');
        modal.className = 'confirm-modal';
        modal.innerHTML = `
            <div class="confirm-overlay" onclick="closeConfirm()"></div>
            <div class="confirm-dialog">
                <div class="confirm-header">
                    <h3>${title}</h3>
                </div>
                <div class="confirm-body">
                    <p>${message}</p>
                </div>
                <div class="confirm-footer">
                    <button class="btn btn-secondary" onclick="closeConfirm(false)">Cancel</button>
                    <button class="btn btn-danger" onclick="closeConfirm(true)">Confirm</button>
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

        // Global function to close modal
        window.closeConfirm = (result = false) => {
            modal.remove();
            delete window.closeConfirm;
            resolve(result);
        };
    });
}

/**
 * Copy text to clipboard
 * @param {string} text 
 * @returns {Promise<boolean>}
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (err) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            document.body.removeChild(textArea);
            return true;
        } catch (err) {
            document.body.removeChild(textArea);
            return false;
        }
    }
}

/**
 * Escape HTML to prevent XSS
 * @param {string} unsafe 
 * @returns {string}
 */
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/**
 * Generate unique ID
 * @returns {string}
 */
function generateId() {
    return '_' + Math.random().toString(36).substr(2, 9);
}

/**
 * Get status class based on container state
 * @param {string} state 
 * @returns {string}
 */
function getStatusClass(state) {
    const statusMap = {
        'running': 'healthy',
        'exited': 'unhealthy',
        'created': 'warning',
        'restarting': 'warning',
        'removing': 'warning',
        'paused': 'warning',
        'dead': 'unhealthy'
    };
    return statusMap[state?.toLowerCase()] || 'unknown';
}

/**
 * Get status text based on container state
 * @param {string} state 
 * @returns {string}
 */
function getStatusText(state) {
    const statusMap = {
        'running': 'Running',
        'exited': 'Stopped',
        'created': 'Created',
        'restarting': 'Restarting',
        'removing': 'Removing',
        'paused': 'Paused',
        'dead': 'Dead'
    };
    return statusMap[state?.toLowerCase()] || 'Unknown';
}

/**
 * Add CSS animation classes
 */
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    .toast {
        animation: slideInRight 0.3s ease-out;
    }

    .toast-content {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .toast-close {
        background: none;
        border: none;
        color: inherit;
        cursor: pointer;
        margin-left: auto;
        padding: 0.25rem;
        border-radius: 2px;
    }

    .toast-close:hover {
        background-color: rgba(0,0,0,0.1);
    }

    .confirm-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0,0,0,0.5);
    }

    .confirm-dialog {
        background: white;
        border-radius: 8px;
        min-width: 400px;
        max-width: 500px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        position: relative;
    }

    .confirm-header {
        padding: 1rem 1.5rem;
        border-bottom: 1px solid #dee2e6;
    }

    .confirm-header h3 {
        margin: 0;
        color: #343a40;
    }

    .confirm-body {
        padding: 1.5rem;
    }

    .confirm-footer {
        padding: 1rem 1.5rem;
        border-top: 1px solid #dee2e6;
        display: flex;
        gap: 1rem;
        justify-content: flex-end;
    }

    @media (max-width: 480px) {
        .confirm-dialog {
            min-width: 90vw;
        }
        
        .toast {
            min-width: 90vw;
            right: 5vw;
        }
    }
`;
document.head.appendChild(style);

// Export utilities to global scope
window.Utils = {
    formatBytes,
    formatUptime,
    formatRelativeTime,
    debounce,
    throttle,
    showToast,
    showLoading,
    hideLoading,
    confirmAction,
    copyToClipboard,
    escapeHtml,
    generateId,
    getStatusClass,
    getStatusText
};
