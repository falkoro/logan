/**
 * Loading Manager for modular data loading
 * Handles progressive loading and better user experience
 */

class LoadingManager {
    constructor() {
        this.loadingStates = new Map();
        this.timeouts = new Map();
    }

    /**
     * Show loading state for a specific component
     */
    showLoading(componentId, message = 'Loading...') {
        const element = document.getElementById(componentId);
        if (!element) return;

        this.loadingStates.set(componentId, true);
        
        // Clear any existing timeout
        if (this.timeouts.has(componentId)) {
            clearTimeout(this.timeouts.get(componentId));
        }

        // Add loading spinner or skeleton
        const existingSpinner = element.querySelector('.loading-spinner');
        if (!existingSpinner) {
            const spinner = this.createLoadingSpinner(message);
            element.innerHTML = '';
            element.appendChild(spinner);
        }
    }

    /**
     * Hide loading state for a specific component
     */
    hideLoading(componentId) {
        this.loadingStates.set(componentId, false);
        
        // Clear timeout
        if (this.timeouts.has(componentId)) {
            clearTimeout(this.timeouts.get(componentId));
            this.timeouts.delete(componentId);
        }
    }

    /**
     * Show loading with timeout (automatically hide after delay)
     */
    showLoadingWithTimeout(componentId, message = 'Loading...', timeout = 10000) {
        this.showLoading(componentId, message);
        
        const timeoutId = setTimeout(() => {
            if (this.loadingStates.get(componentId)) {
                this.hideLoading(componentId);
                this.showError(componentId, 'Loading timed out');
            }
        }, timeout);
        
        this.timeouts.set(componentId, timeoutId);
    }

    /**
     * Show error state
     */
    showError(componentId, message = 'Failed to load data') {
        const element = document.getElementById(componentId);
        if (!element) return;

        this.hideLoading(componentId);
        
        element.innerHTML = `
            <div class="flex flex-col items-center justify-center p-8 text-center">
                <div class="bg-red-100 dark:bg-red-900 p-3 rounded-full mb-4">
                    <i class="fas fa-exclamation-triangle text-red-600 dark:text-red-400 text-xl"></i>
                </div>
                <p class="text-gray-600 dark:text-gray-400 mb-4">${message}</p>
                <button onclick="location.reload()" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                    <i class="fas fa-refresh mr-2"></i>Retry
                </button>
            </div>
        `;
    }

    /**
     * Show empty state
     */
    showEmpty(componentId, message = 'No data available', icon = 'fa-inbox') {
        const element = document.getElementById(componentId);
        if (!element) return;

        this.hideLoading(componentId);
        
        element.innerHTML = `
            <div class="flex flex-col items-center justify-center p-8 text-center">
                <div class="bg-gray-100 dark:bg-gray-800 p-3 rounded-full mb-4">
                    <i class="fas ${icon} text-gray-400 text-xl"></i>
                </div>
                <p class="text-gray-500 dark:text-gray-400">${message}</p>
            </div>
        `;
    }

    /**
     * Create loading spinner element
     */
    createLoadingSpinner(message = 'Loading...') {
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner flex flex-col items-center justify-center p-8 text-center';
        spinner.innerHTML = `
            <div class="animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent mb-4"></div>
            <p class="text-gray-500 dark:text-gray-400 text-sm">${message}</p>
        `;
        return spinner;
    }

    /**
     * Create skeleton loader for cards
     */
    createCardSkeleton() {
        const skeleton = document.createElement('div');
        skeleton.className = 'animate-pulse space-y-3 p-4';
        skeleton.innerHTML = `
            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3"></div>
        `;
        return skeleton;
    }

    /**
     * Check if component is currently loading
     */
    isLoading(componentId) {
        return this.loadingStates.get(componentId) || false;
    }

    /**
     * Progressive loading for multiple components
     */
    async loadProgressively(loadTasks) {
        const results = [];
        
        for (const task of loadTasks) {
            try {
                this.showLoading(task.componentId, task.message || 'Loading...');
                const result = await task.loadFunction();
                this.hideLoading(task.componentId);
                results.push({ success: true, componentId: task.componentId, data: result });
            } catch (error) {
                console.error(`Failed to load ${task.componentId}:`, error);
                this.showError(task.componentId, task.errorMessage || 'Failed to load data');
                results.push({ success: false, componentId: task.componentId, error });
            }
            
            // Small delay between loads to prevent overwhelming
            if (task.delay) {
                await new Promise(resolve => setTimeout(resolve, task.delay));
            }
        }
        
        return results;
    }

    /**
     * Load with retry mechanism
     */
    async loadWithRetry(componentId, loadFunction, retries = 3, delay = 1000) {
        for (let attempt = 1; attempt <= retries; attempt++) {
            try {
                this.showLoading(componentId, attempt > 1 ? `Loading... (attempt ${attempt}/${retries})` : 'Loading...');
                const result = await loadFunction();
                this.hideLoading(componentId);
                return result;
            } catch (error) {
                if (attempt === retries) {
                    this.showError(componentId, `Failed to load after ${retries} attempts`);
                    throw error;
                }
                
                // Wait before retrying
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }
}

// Global loading manager instance
const loadingManager = new LoadingManager();

// Helper functions for backward compatibility
function showLoadingSpinner(show, componentId = 'main-content') {
    if (show) {
        loadingManager.showLoading(componentId);
    } else {
        loadingManager.hideLoading(componentId);
    }
}

function showLoadingState(componentId, show, message = 'Loading...') {
    if (show) {
        loadingManager.showLoading(componentId, message);
    } else {
        loadingManager.hideLoading(componentId);
    }
}
