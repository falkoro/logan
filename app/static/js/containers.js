/**
 * Containers tab functionality
 * Handles Docker container management with drag & drop and resizing
 */

let containersData = {
    containers: [],
    selectedContainers: new Set(),
    filteredContainers: [],
    sortBy: 'name',
    sortOrder: 'asc',
    filterStatus: 'all',
    searchQuery: '',
    viewMode: 'grid', // 'grid' or 'list'
    containerSizes: new Map() // Store custom sizes for containers
};

// Drag and drop state
let dragState = {
    isDragging: false,
    draggedElement: null,
    startX: 0,
    startY: 0,
    offsetX: 0,
    offsetY: 0
};

// Resize state
let resizeState = {
    isResizing: false,
    resizeElement: null,
    startX: 0,
    startY: 0,
    startWidth: 0,
    startHeight: 0
};

/**
 * Initialize containers tab
 */
function initContainersTab() {
    console.log('Initializing containers tab...');
    setupContainerFilters();
    setupContainerSearch();
    setupBulkActions();
    setupDragAndDrop();
    setupViewMode();
    loadContainers();
}

/**
 * Setup view mode switching
 */
function setupViewMode() {
    containersData.viewMode = localStorage.getItem('containersViewMode') || 'grid';
    updateViewModeButtons();
}

/**
 * Set view mode
 */
function setViewMode(mode) {
    containersData.viewMode = mode;
    localStorage.setItem('containersViewMode', mode);
    updateViewModeButtons();
    renderContainers();
}

/**
 * Update view mode buttons
 */
function updateViewModeButtons() {
    const gridBtn = document.getElementById('grid-view-btn');
    const listBtn = document.getElementById('list-view-btn');
    const container = document.getElementById('containers-grid');
    
    if (gridBtn && listBtn && container) {
        container.setAttribute('data-view-mode', containersData.viewMode);
        
        if (containersData.viewMode === 'grid') {
            gridBtn.className = 'px-3 py-1.5 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors';
            listBtn.className = 'px-3 py-1.5 text-xs bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors';
        } else {
            gridBtn.className = 'px-3 py-1.5 text-xs bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors';
            listBtn.className = 'px-3 py-1.5 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors';
        }
    }
}

/**
 * Load containers data
 */
async function loadContainers() {
    try {
        showLoadingState(true);
        
        // Load basic container info first for quick display
        const quickData = await getContainersData();
        containersData.containers = quickData.data.containers || [];
        
        if (containersData.containers.length === 0) {
            showEmptyState();
            return;
        }
        
        // Update display with basic info
        applyFiltersAndSort();
        renderContainers();
        updateContainerCounts();
        
        // Hide loading for basic data
        showLoadingState(false);
        
        // Then load detailed stats in background
        setTimeout(async () => {
            try {
                const detailedData = await getContainersData();
                containersData.containers = detailedData.data.containers || [];
                applyFiltersAndSort();
                renderContainers();
                updateContainerCounts();
            } catch (error) {
                console.warn('Failed to load detailed container stats:', error);
            }
        }, 500);
        
    } catch (error) {
        console.error('Failed to load containers:', error);
        showToast('Failed to load containers', 'error');
        containersData.containers = [];
        showEmptyState();
        showLoadingState(false);
    }
}

/**
 * Show loading state
 */
function showLoadingState(show) {
    const loadingState = document.getElementById('loading-state');
    const emptyState = document.getElementById('empty-state');
    const grid = document.getElementById('containers-grid');
    
    if (loadingState) {
        if (show) {
            loadingState.classList.remove('hidden');
            emptyState?.classList.add('hidden');
            // Clear grid content except states
            const containers = grid.querySelectorAll('.container-card');
            containers.forEach(card => card.remove());
        } else {
            loadingState.classList.add('hidden');
        }
    }
}

/**
 * Show empty state
 */
function showEmptyState() {
    const loadingState = document.getElementById('loading-state');
    const emptyState = document.getElementById('empty-state');
    
    if (emptyState) {
        loadingState?.classList.add('hidden');
        emptyState.classList.remove('hidden');
    }
}

/**
 * Setup drag and drop functionality
 */
function setupDragAndDrop() {
    const grid = document.getElementById('containers-grid');
    if (!grid) return;
    
    // Global mouse events for dragging and resizing
    document.addEventListener('mousedown', handleMouseDown);
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('selectstart', (e) => {
        if (dragState.isDragging || resizeState.isResizing) {
            e.preventDefault();
        }
    });
}

/**
 * Handle mouse down for drag/resize
 */
function handleMouseDown(e) {
    const containerCard = e.target.closest('.container-card');
    const resizeHandle = e.target.closest('.resize-handle');
    const dragHandle = e.target.closest('.drag-handle');
    
    if (resizeHandle && containerCard) {
        e.preventDefault();
        startResize(e, containerCard);
    } else if (dragHandle && containerCard) {
        e.preventDefault();
        startDrag(e, containerCard);
    }
}

/**
 * Handle mouse move for drag/resize
 */
function handleMouseMove(e) {
    if (resizeState.isResizing) {
        e.preventDefault();
        performResize(e);
    } else if (dragState.isDragging) {
        e.preventDefault();
        performDrag(e);
    }
}

/**
 * Handle mouse up for drag/resize
 */
function handleMouseUp(e) {
    if (resizeState.isResizing) {
        stopResize();
    } else if (dragState.isDragging) {
        stopDrag();
    }
}

/**
 * Start dragging a container
 */
function startDrag(e, element) {
    dragState.isDragging = true;
    dragState.draggedElement = element;
    
    const rect = element.getBoundingClientRect();
    dragState.offsetX = e.clientX - rect.left;
    dragState.offsetY = e.clientY - rect.top;
    
    element.style.position = 'fixed';
    element.style.zIndex = '1000';
    element.style.pointerEvents = 'none';
    element.classList.add('dragging');
    
    document.body.style.cursor = 'grabbing';
}

/**
 * Perform drag operation
 */
function performDrag(e) {
    if (!dragState.draggedElement) return;
    
    const x = e.clientX - dragState.offsetX;
    const y = e.clientY - dragState.offsetY;
    
    dragState.draggedElement.style.left = x + 'px';
    dragState.draggedElement.style.top = y + 'px';
}

/**
 * Stop dragging
 */
function stopDrag() {
    if (!dragState.draggedElement) return;
    
    const element = dragState.draggedElement;
    
    // Reset styles
    element.style.position = '';
    element.style.zIndex = '';
    element.style.left = '';
    element.style.top = '';
    element.style.pointerEvents = '';
    element.classList.remove('dragging');
    
    document.body.style.cursor = '';
    
    // Reset drag state
    dragState.isDragging = false;
    dragState.draggedElement = null;
}

/**
 * Start resizing a container
 */
function startResize(e, element) {
    resizeState.isResizing = true;
    resizeState.resizeElement = element;
    resizeState.startX = e.clientX;
    resizeState.startY = e.clientY;
    
    const rect = element.getBoundingClientRect();
    resizeState.startWidth = rect.width;
    resizeState.startHeight = rect.height;
    
    element.classList.add('resizing');
    document.body.style.cursor = 'se-resize';
}

/**
 * Perform resize operation
 */
function performResize(e) {
    if (!resizeState.resizeElement) return;
    
    const deltaX = e.clientX - resizeState.startX;
    const deltaY = e.clientY - resizeState.startY;
    
    const newWidth = Math.max(250, resizeState.startWidth + deltaX);
    const newHeight = Math.max(200, resizeState.startHeight + deltaY);
    
    resizeState.resizeElement.style.width = newWidth + 'px';
    resizeState.resizeElement.style.height = newHeight + 'px';
}

/**
 * Stop resizing
 */
function stopResize() {
    if (!resizeState.resizeElement) return;
    
    const element = resizeState.resizeElement;
    const containerId = element.dataset.containerId;
    
    // Save the custom size
    const rect = element.getBoundingClientRect();
    containersData.containerSizes.set(containerId, {
        width: rect.width,
        height: rect.height
    });
    
    element.classList.remove('resizing');
    document.body.style.cursor = '';
    
    // Reset resize state
    resizeState.isResizing = false;
    resizeState.resizeElement = null;
}

/**
 * Apply filters and sorting to containers
 */
function applyFiltersAndSort() {
    let filtered = [...containersData.containers];
    
    // Apply status filter
    if (containersData.filterStatus !== 'all') {
        filtered = filtered.filter(container => {
            switch (containersData.filterStatus) {
                case 'running': return container.is_running;
                case 'stopped': return !container.is_running;
                case 'healthy': return container.is_healthy;
                case 'unhealthy': return !container.is_healthy;
                default: return true;
            }
        });
    }
    
    // Apply search filter
    if (containersData.searchQuery) {
        const query = containersData.searchQuery.toLowerCase();
        filtered = filtered.filter(container =>
            container.name.toLowerCase().includes(query) ||
            container.image.toLowerCase().includes(query) ||
            (container.ports && container.ports.some(port => port.includes(query)))
        );
    }
    
    // Apply sorting
    filtered.sort((a, b) => {
        let aValue, bValue;
        
        switch (containersData.sortBy) {
            case 'name':
                aValue = a.name.toLowerCase();
                bValue = b.name.toLowerCase();
                break;
            case 'status':
                aValue = a.is_running ? 1 : 0;
                bValue = b.is_running ? 1 : 0;
                break;
            case 'image':
                aValue = a.image.toLowerCase();
                bValue = b.image.toLowerCase();
                break;
            case 'created':
                aValue = new Date(a.created);
                bValue = new Date(b.created);
                break;
            case 'cpu':
                aValue = a.stats?.cpu_percent || 0;
                bValue = b.stats?.cpu_percent || 0;
                break;
            case 'memory':
                aValue = a.stats?.memory_percent || 0;
                bValue = b.stats?.memory_percent || 0;
                break;
            default:
                aValue = a.name.toLowerCase();
                bValue = b.name.toLowerCase();
        }
        
        if (containersData.sortOrder === 'desc') {
            return aValue < bValue ? 1 : -1;
        }
        return aValue > bValue ? 1 : -1;
    });
    
    containersData.filteredContainers = filtered;
}

/**
 * Render containers in grid or list view
 */
function renderContainers() {
    const grid = document.getElementById('containers-grid');
    if (!grid) return;
    
    // Remove existing container cards
    const existingCards = grid.querySelectorAll('.container-card');
    existingCards.forEach(card => card.remove());
    
    if (containersData.filteredContainers.length === 0) {
        showEmptyState();
        return;
    }
    
    // Hide states
    const loadingState = document.getElementById('loading-state');
    const emptyState = document.getElementById('empty-state');
    loadingState?.classList.add('hidden');
    emptyState?.classList.add('hidden');
    
    // Create container cards
    containersData.filteredContainers.forEach(containerData => {
        const cardElement = createContainerCard(containerData);
        grid.appendChild(cardElement);
    });
    
    // Apply view mode styles
    applyViewModeStyles();
}

/**
 * Apply view mode specific styles
 */
function applyViewModeStyles() {
    const grid = document.getElementById('containers-grid');
    if (!grid) return;
    
    if (containersData.viewMode === 'grid') {
        grid.className = 'p-6 min-h-96 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6';
    } else {
        grid.className = 'p-6 min-h-96 space-y-4';
    }
}

/**
 * Create a container card element
 */
function createContainerCard(container) {
    const isSelected = containersData.selectedContainers.has(container.id);
    const customSize = containersData.containerSizes.get(container.id);
    
    const card = document.createElement('div');
    card.className = `container-card bg-white dark:bg-gray-800 rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 relative ${isSelected ? 'ring-2 ring-blue-500 border-blue-500' : ''} ${containersData.viewMode === 'grid' ? 'min-h-64' : ''}`;
    card.dataset.containerId = container.id;
    card.dataset.status = container.is_running ? 'running' : 'stopped';
    card.dataset.health = container.is_healthy ? 'healthy' : 'unhealthy';
    
    // Apply custom size if exists
    if (customSize && containersData.viewMode === 'grid') {
        card.style.width = customSize.width + 'px';
        card.style.height = customSize.height + 'px';
        card.style.minHeight = 'auto';
    }
    
    card.innerHTML = getContainerCardHTML(container);
    
    return card;
}

/**
 * Get HTML for empty containers state
 */
function getEmptyContainersHTML() {
    const hasContainers = containersData.containers.length > 0;
    
    if (!hasContainers) {
        return `
            <div class="text-center py-12">
                <i class="fas fa-box-open text-6xl text-gray-300 dark:text-gray-600 mb-4"></i>
                <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">No containers found</h3>
                <p class="text-gray-500 dark:text-gray-400 mb-6">No Docker containers are available on the remote host.</p>
                <button onclick="loadContainers()" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                    <i class="fas fa-refresh mr-2"></i>Refresh
                </button>
            </div>
        `;
    }
    
    return `
        <div class="text-center py-12">
            <i class="fas fa-filter text-6xl text-gray-300 dark:text-gray-600 mb-4"></i>
            <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">No containers match your filters</h3>
            <p class="text-gray-500 dark:text-gray-400 mb-6">Try adjusting your search or filter settings.</p>
            <button onclick="clearContainerFilters()" class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors">
                <i class="fas fa-times mr-2"></i>Clear Filters
            </button>
        </div>
    `;
}

/**
 * Get HTML for container card
 */
function getContainerCardHTML(container) {
    const isSelected = containersData.selectedContainers.has(container.id);
    const statusIcon = container.is_running ? 'play' : 'stop';
    const statusColor = container.is_running ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400';
    const healthIcon = container.is_healthy ? 'check-circle' : 'exclamation-circle';
    const healthColor = container.is_healthy ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400';
    
    const isGridView = containersData.viewMode === 'grid';
    
    return `
        <!-- Drag Handle (only in grid view) -->
        ${isGridView ? `
            <div class="drag-handle absolute top-2 left-2 p-1 rounded bg-gray-100 dark:bg-gray-700 opacity-50 hover:opacity-100 transition-opacity cursor-grab active:cursor-grabbing z-10">
                <i class="fas fa-grip-vertical text-xs text-gray-600 dark:text-gray-400"></i>
            </div>
        ` : ''}
        
        <!-- Resize Handle (only in grid view) -->
        ${isGridView ? `
            <div class="resize-handle absolute bottom-0 right-0 w-4 h-4 cursor-se-resize z-10">
                <div class="w-full h-full flex items-end justify-end">
                    <div class="w-3 h-3 bg-blue-500 opacity-50 hover:opacity-100 transition-opacity" style="clip-path: polygon(100% 0, 0 100%, 100% 100%)"></div>
                </div>
            </div>
        ` : ''}
        
        <div class="p-4 h-full flex flex-col">
            <!-- Header -->
            <div class="flex items-center justify-between mb-3">
                <div class="flex items-center space-x-3 min-w-0 flex-1">
                    <input type="checkbox" ${isSelected ? 'checked' : ''} 
                           onchange="toggleContainerSelection('${container.id}')"
                           class="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500">
                    <div class="min-w-0 flex-1">
                        <h3 class="text-lg font-semibold text-gray-900 dark:text-white truncate" title="${container.name}">
                            ${container.name}
                        </h3>
                        <p class="text-sm text-gray-500 dark:text-gray-400 truncate" title="${container.image}">
                            ${container.image}
                        </p>
                    </div>
                </div>
                <div class="flex items-center space-x-2 ml-2">
                    <div class="flex items-center space-x-1">
                        <i class="fas fa-${statusIcon} ${statusColor}" title="${container.is_running ? 'Running' : 'Stopped'}"></i>
                        <i class="fas fa-${healthIcon} ${healthColor}" title="${container.is_healthy ? 'Healthy' : 'Unhealthy'}"></i>
                    </div>
                    <button onclick="showContainerActionMenu('${container.id}')" 
                            class="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                        <i class="fas fa-ellipsis-v text-gray-400"></i>
                    </button>
                </div>
            </div>
            
            <!-- Status Badges -->
            <div class="flex flex-wrap gap-2 mb-3">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${container.is_running ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'}">
                    <i class="fas fa-${statusIcon} mr-1"></i>
                    ${container.is_running ? 'Running' : 'Stopped'}
                </span>
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${container.is_healthy ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'}">
                    <i class="fas fa-${healthIcon} mr-1"></i>
                    ${container.is_healthy ? 'Healthy' : 'Unhealthy'}
                </span>
            </div>
            
            <!-- Stats (if available) -->
            ${container.stats ? `
                <div class="grid ${isGridView ? 'grid-cols-1' : 'grid-cols-3'} gap-3 mb-3">
                    <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                        <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-1">CPU Usage</p>
                        <div class="flex items-center">
                            <p class="text-sm font-semibold text-gray-900 dark:text-white">${container.stats.cpu_percent.toFixed(1)}%</p>
                            <div class="ml-2 flex-1 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                                <div class="bg-blue-500 h-2 rounded-full" style="width: ${Math.min(100, container.stats.cpu_percent)}%"></div>
                            </div>
                        </div>
                    </div>
                    ${!isGridView ? `
                        <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                            <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-1">Memory</p>
                            <div class="flex items-center">
                                <p class="text-sm font-semibold text-gray-900 dark:text-white">${container.stats.memory_percent.toFixed(1)}%</p>
                                <div class="ml-2 flex-1 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                                    <div class="bg-green-500 h-2 rounded-full" style="width: ${Math.min(100, container.stats.memory_percent)}%"></div>
                                </div>
                            </div>
                        </div>
                        <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                            <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-1">Network I/O</p>
                            <p class="text-sm font-semibold text-gray-900 dark:text-white">${formatBytes(container.stats.network_rx + container.stats.network_tx)}</p>
                        </div>
                    ` : ''}
                </div>
            ` : ''}
            
            <!-- Ports -->
            ${container.ports && container.ports.length > 0 ? `
                <div class="mb-3">
                    <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-2">Exposed Ports</p>
                    <div class="flex flex-wrap gap-1">
                        ${container.ports.slice(0, 3).map(port => `
                            <span class="inline-flex items-center px-2 py-1 rounded text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 font-mono">
                                ${port}
                            </span>
                        `).join('')}
                        ${container.ports.length > 3 ? `
                            <span class="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300">
                                +${container.ports.length - 3} more
                            </span>
                        ` : ''}
                    </div>
                </div>
            ` : ''}
            
            <!-- Actions -->
            <div class="mt-auto pt-3 border-t border-gray-200 dark:border-gray-600">
                <div class="flex items-center justify-between ${isGridView ? 'flex-col space-y-2' : 'space-x-2'}">
                    <div class="flex space-x-2 ${isGridView ? 'w-full' : ''}">
                        ${container.is_running ? `
                            <button onclick="stopContainer('${container.id}')" 
                                    class="px-3 py-1.5 text-xs bg-red-600 text-white rounded hover:bg-red-700 transition-colors ${isGridView ? 'flex-1' : ''}">
                                <i class="fas fa-stop mr-1"></i>Stop
                            </button>
                            <button onclick="restartContainer('${container.id}')" 
                                    class="px-3 py-1.5 text-xs bg-orange-600 text-white rounded hover:bg-orange-700 transition-colors ${isGridView ? 'flex-1' : ''}">
                                <i class="fas fa-redo mr-1"></i>Restart
                            </button>
                        ` : `
                            <button onclick="startContainer('${container.id}')" 
                                    class="px-3 py-1.5 text-xs bg-green-600 text-white rounded hover:bg-green-700 transition-colors ${isGridView ? 'flex-1' : ''}">
                                <i class="fas fa-play mr-1"></i>Start
                            </button>
                        `}
                    </div>
                    <div class="flex space-x-2 ${isGridView ? 'w-full' : ''}">
                        <button onclick="showContainerLogs('${container.id}')" 
                                class="px-3 py-1.5 text-xs bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors ${isGridView ? 'flex-1' : ''}">
                            <i class="fas fa-file-alt mr-1"></i>Logs
                        </button>
                        <button onclick="showContainerDetails('${container.id}')" 
                                class="px-3 py-1.5 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors ${isGridView ? 'flex-1' : ''}">
                            <i class="fas fa-info mr-1"></i>Details
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Setup container filters
 */
function setupContainerFilters() {
    const statusFilter = document.getElementById('status-filter');
    
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            containersData.filterStatus = this.value;
            applyFiltersAndSort();
            renderContainers();
            updateContainerCounts();
        });
    }
}

/**
 * Setup container search
 */
function setupContainerSearch() {
    const searchInput = document.getElementById('container-search');
    
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                containersData.searchQuery = this.value.trim();
                applyFiltersAndSort();
                renderContainers();
                updateContainerCounts();
            }, 300);
        });
    }
}

/**
 * Setup bulk actions
 */
function setupBulkActions() {
    const selectAllCheckbox = document.getElementById('select-all');
    
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            if (this.checked) {
                containersData.filteredContainers.forEach(container => {
                    containersData.selectedContainers.add(container.id);
                });
            } else {
                containersData.selectedContainers.clear();
            }
            renderContainers();
            updateBulkActionsVisibility();
        });
    }
}

/**
 * Toggle container selection
 */
function toggleContainerSelection(containerId) {
    if (containersData.selectedContainers.has(containerId)) {
        containersData.selectedContainers.delete(containerId);
    } else {
        containersData.selectedContainers.add(containerId);
    }
    
    updateBulkActionsVisibility();
    updateSelectAllCheckbox();
    renderContainers();
}

/**
 * Update container counts in the statistics
 */
function updateContainerCounts() {
    const totalElement = document.getElementById('total-containers');
    const runningElement = document.getElementById('running-containers-count');
    const stoppedElement = document.getElementById('stopped-containers-count');
    const unhealthyElement = document.getElementById('unhealthy-containers-count');
    
    const total = containersData.containers.length;
    const running = containersData.containers.filter(c => c.is_running).length;
    const stopped = total - running;
    const unhealthy = containersData.containers.filter(c => !c.is_healthy).length;
    
    if (totalElement) totalElement.textContent = total;
    if (runningElement) runningElement.textContent = running;
    if (stoppedElement) stoppedElement.textContent = stopped;
    if (unhealthyElement) unhealthyElement.textContent = unhealthy;
}

/**
 * Update bulk actions visibility
 */
function updateBulkActionsVisibility() {
    const bulkActionsBtn = document.getElementById('bulk-actions-btn');
    const selectedCount = containersData.selectedContainers.size;
    
    if (bulkActionsBtn) {
        bulkActionsBtn.disabled = selectedCount === 0;
        if (selectedCount > 0) {
            bulkActionsBtn.innerHTML = `<i class="fas fa-list mr-2"></i>Actions (${selectedCount})`;
        } else {
            bulkActionsBtn.innerHTML = '<i class="fas fa-list mr-2"></i>Bulk Actions';
        }
    }
}

/**
 * Update select all checkbox
 */
function updateSelectAllCheckbox() {
    const selectAllCheckbox = document.getElementById('select-all');
    
    if (selectAllCheckbox) {
        const totalFiltered = containersData.filteredContainers.length;
        const selectedCount = containersData.selectedContainers.size;
        
        selectAllCheckbox.checked = totalFiltered > 0 && selectedCount === totalFiltered;
        selectAllCheckbox.indeterminate = selectedCount > 0 && selectedCount < totalFiltered;
    }
}

/**
 * Update bulk actions visibility
 */
function updateBulkActionsVisibility() {
    const bulkActions = document.getElementById('bulk-actions');
    const selectedCount = document.getElementById('selected-count');
    
    if (bulkActions && selectedCount) {
        const count = containersData.selectedContainers.size;
        
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
function updateSelectAllCheckbox() {
    const selectAllCheckbox = document.getElementById('select-all-containers');
    
    if (selectAllCheckbox) {
        const totalFiltered = containersData.filteredContainers.length;
        const selectedCount = containersData.selectedContainers.size;
        
        selectAllCheckbox.checked = totalFiltered > 0 && selectedCount === totalFiltered;
        selectAllCheckbox.indeterminate = selectedCount > 0 && selectedCount < totalFiltered;
    }
}

/**
 * Update container counts
 */
function updateContainerCounts() {
    const totalCount = document.getElementById('total-containers-count');
    const filteredCount = document.getElementById('filtered-containers-count');
    
    if (totalCount) {
        totalCount.textContent = containersData.containers.length;
    }
    
    if (filteredCount) {
        filteredCount.textContent = containersData.filteredContainers.length;
    }
}

/**
 * Clear container filters
 */
function clearContainerFilters() {
    containersData.filterStatus = 'all';
    containersData.searchQuery = '';
    containersData.sortBy = 'name';
    containersData.sortOrder = 'asc';
    
    // Reset UI elements
    const statusFilter = document.getElementById('container-status-filter');
    const searchInput = document.getElementById('container-search');
    const sortSelect = document.getElementById('container-sort');
    
    if (statusFilter) statusFilter.value = 'all';
    if (searchInput) searchInput.value = '';
    if (sortSelect) sortSelect.value = 'name:asc';
    
    applyFiltersAndSort();
    renderContainers();
    updateContainerCounts();
}

// Container Actions
async function startContainer(containerId) {
    try {
        await makeRequest(`/api/containers/${containerId}/start`, { method: 'POST' });
        showToast('Container started successfully', 'success');
        await loadContainers();
    } catch (error) {
        console.error('Failed to start container:', error);
        showToast('Failed to start container', 'error');
    }
}

async function stopContainer(containerId) {
    try {
        await makeRequest(`/api/containers/${containerId}/stop`, { method: 'POST' });
        showToast('Container stopped successfully', 'success');
        await loadContainers();
    } catch (error) {
        console.error('Failed to stop container:', error);
        showToast('Failed to stop container', 'error');
    }
}

async function restartContainer(containerId) {
    try {
        await makeRequest(`/api/containers/${containerId}/restart`, { method: 'POST' });
        showToast('Container restarted successfully', 'success');
        await loadContainers();
    } catch (error) {
        console.error('Failed to restart container:', error);
        showToast('Failed to restart container', 'error');
    }
}

// Bulk Actions
async function startSelectedContainers() {
    if (containersData.selectedContainers.size === 0) return;
    
    try {
        const containerIds = Array.from(containersData.selectedContainers);
        await makeRequest('/api/containers/bulk/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ container_ids: containerIds })
        });
        
        showToast(`Started ${containerIds.length} containers`, 'success');
        containersData.selectedContainers.clear();
        updateBulkActionsVisibility();
        await loadContainers();
    } catch (error) {
        console.error('Failed to start containers:', error);
        showToast('Failed to start some containers', 'error');
    }
}

async function stopSelectedContainers() {
    if (containersData.selectedContainers.size === 0) return;
    
    try {
        const containerIds = Array.from(containersData.selectedContainers);
        await makeRequest('/api/containers/bulk/stop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ container_ids: containerIds })
        });
        
        showToast(`Stopped ${containerIds.length} containers`, 'success');
        containersData.selectedContainers.clear();
        updateBulkActionsVisibility();
        await loadContainers();
    } catch (error) {
        console.error('Failed to stop containers:', error);
        showToast('Failed to stop some containers', 'error');
    }
}

async function restartSelectedContainers() {
    if (containersData.selectedContainers.size === 0) return;
    
    try {
        const containerIds = Array.from(containersData.selectedContainers);
        await makeRequest('/api/containers/bulk/restart', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ container_ids: containerIds })
        });
        
        showToast(`Restarted ${containerIds.length} containers`, 'success');
        containersData.selectedContainers.clear();
        updateBulkActionsVisibility();
        await loadContainers();
    } catch (error) {
        console.error('Failed to restart containers:', error);
        showToast('Failed to restart some containers', 'error');
    }
}

// Container Details and Logs
function showContainerDetails(containerId) {
    // This will be implemented with a modal
    console.log('Show container details:', containerId);
}

function showContainerLogs(containerId) {
    // This will show logs tab with specific container
    showTab('logs');
    if (typeof setLogContainer === 'function') {
        setLogContainer(containerId);
    }
}

function showContainerActionMenu(containerId) {
    // This will be implemented with a dropdown menu
    console.log('Show container action menu:', containerId);
}

// Format bytes helper
function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (typeof currentTab !== 'undefined' && currentTab === 'containers') {
        initContainersTab();
    }
});

// WebSocket handlers for containers
if (typeof io !== 'undefined') {
    document.addEventListener('DOMContentLoaded', function() {
        if (typeof socket !== 'undefined' && socket) {
            socket.on('container_update', function(data) {
                if (currentTab === 'containers') {
                    containersData.containers = data.containers || [];
                    applyFiltersAndSort();
                    renderContainers();
                    updateContainerCounts();
                }
            });
        }
    });
}
