/**
 * Mock data for frontend testing and development
 * Provides sample data when APIs are unavailable
 */

const mockData = {
    containers: [
        {
            id: 'mock-plex',
            name: 'plex-media-server',
            image: 'plexinc/pms-docker:latest',
            is_running: true,
            is_healthy: true,
            created: '2025-01-15T10:30:00Z',
            uptime: '7 days, 14 hours',
            primary_port: '32400',
            ports: ['32400:32400', '3005:3005', '8324:8324'],
            stats: {
                cpu_percent: 15.2,
                memory_percent: 23.8,
                memory_usage: 512000000,
                memory_limit: 2048000000,
                network_rx: 1024000,
                network_tx: 2048000
            }
        },
        {
            id: 'mock-sonarr',
            name: 'sonarr',
            image: 'linuxserver/sonarr:latest',
            is_running: true,
            is_healthy: true,
            created: '2025-01-14T09:15:00Z',
            uptime: '8 days, 5 hours',
            primary_port: '8989',
            ports: ['8989:8989'],
            stats: {
                cpu_percent: 5.8,
                memory_percent: 12.4,
                memory_usage: 256000000,
                memory_limit: 1024000000,
                network_rx: 512000,
                network_tx: 1024000
            }
        },
        {
            id: 'mock-radarr',
            name: 'radarr',
            image: 'linuxserver/radarr:latest',
            is_running: true,
            is_healthy: false,
            created: '2025-01-13T16:20:00Z',
            uptime: '9 days, 2 hours',
            primary_port: '7878',
            ports: ['7878:7878'],
            stats: {
                cpu_percent: 3.2,
                memory_percent: 8.7,
                memory_usage: 128000000,
                memory_limit: 512000000,
                network_rx: 256000,
                network_tx: 512000
            }
        },
        {
            id: 'mock-nginx',
            name: 'nginx-proxy',
            image: 'nginx:alpine',
            is_running: false,
            is_healthy: false,
            created: '2025-01-12T11:45:00Z',
            uptime: null,
            primary_port: null,
            ports: [],
            stats: null
        },
        {
            id: 'mock-redis',
            name: 'redis-cache',
            image: 'redis:7-alpine',
            is_running: true,
            is_healthy: true,
            created: '2025-01-11T14:30:00Z',
            uptime: '11 days, 8 hours',
            primary_port: '6379',
            ports: ['6379:6379'],
            stats: {
                cpu_percent: 1.5,
                memory_percent: 4.2,
                memory_usage: 64000000,
                memory_limit: 256000000,
                network_rx: 128000,
                network_tx: 256000
            }
        }
    ],

    systemInfo: {
        hostname: 'docker-host-demo',
        platform: 'Linux 5.15.0-generic',
        uptime_formatted: '15 days, 4 hours, 23 minutes',
        cpu: {
            percent: 45.3,
            load_avg: [1.2, 1.5, 1.8],
            cores: 8
        },
        memory: {
            percent: 67.8,
            total: 16777216000,
            used: 11374182400,
            available: 5403033600
        },
        summary: {
            disk_usage_percent: 73.2,
            total_disk: 1000000000000,
            used_disk: 732000000000
        },
        network: {
            bytes_sent: 1073741824,
            bytes_recv: 2147483648
        }
    },

    services: [
        {
            name: 'Plex Media Server',
            url: 'http://localhost:32400',
            status: 'healthy',
            category: 'media',
            description: 'Media streaming server'
        },
        {
            name: 'Sonarr',
            url: 'http://localhost:8989',
            status: 'healthy',
            category: 'media',
            description: 'TV show management'
        },
        {
            name: 'Radarr',
            url: 'http://localhost:7878',
            status: 'unhealthy',
            category: 'media',
            description: 'Movie management'
        },
        {
            name: 'Nginx Proxy',
            url: 'http://localhost:80',
            status: 'offline',
            category: 'infrastructure',
            description: 'Reverse proxy server'
        }
    ]
};

/**
 * Check if we should use mock data
 */
function shouldUseMockData() {
    // Use mock data if localStorage flag is set or if we're in demo mode
    return localStorage.getItem('useMockData') === 'true' || 
           window.location.search.includes('demo=true') ||
           window.location.hostname === 'localhost';
}

/**
 * Get containers data (real or mock)
 */
async function getContainersData(useMock = false) {
    if (useMock || shouldUseMockData()) {
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 500));
        return {
            success: true,
            data: {
                total: mockData.containers.length,
                running: mockData.containers.filter(c => c.is_running).length,
                stopped: mockData.containers.filter(c => !c.is_running).length,
                containers: mockData.containers
            }
        };
    }
    
    try {
        return await makeRequest('/api/containers/overview');
    } catch (error) {
        console.warn('API failed, falling back to mock data:', error);
        return getContainersData(true);
    }
}

/**
 * Get system info data (real or mock)
 */
async function getSystemData(useMock = false) {
    if (useMock || shouldUseMockData()) {
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 300));
        return {
            success: true,
            data: mockData.systemInfo
        };
    }
    
    try {
        return await makeRequest('/api/system/info');
    } catch (error) {
        console.warn('System API failed, falling back to mock data:', error);
        return getSystemData(true);
    }
}

/**
 * Get services data (real or mock)
 */
async function getServicesData(useMock = false) {
    if (useMock || shouldUseMockData()) {
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 400));
        return {
            success: true,
            data: mockData.services
        };
    }
    
    try {
        return await makeRequest('/api/services');
    } catch (error) {
        console.warn('Services API failed, falling back to mock data:', error);
        return getServicesData(true);
    }
}

/**
 * Toggle between real and mock data
 */
function toggleMockData() {
    const currentlyUsingMock = shouldUseMockData();
    localStorage.setItem('useMockData', (!currentlyUsingMock).toString());
    
    // Show notification
    const message = currentlyUsingMock ? 'Switched to real API data' : 'Switched to mock demo data';
    showToast(message, 'info');
    
    // Refresh current tab
    refreshCurrentTabData();
}

// Export for global use
window.mockData = mockData;
window.getContainersData = getContainersData;
window.getSystemData = getSystemData;
window.getServicesData = getServicesData;
window.toggleMockData = toggleMockData;
window.shouldUseMockData = shouldUseMockData;