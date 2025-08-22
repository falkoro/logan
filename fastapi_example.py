"""
FastAPI + Modern Frontend Example
More performant and modern than Flask
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import docker
from typing import List, Dict, Any
import asyncio

app = FastAPI(title="Docker Dashboard API", version="1.0.0")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

class DockerManager:
    def __init__(self):
        try:
            self.client = docker.from_env()
        except docker.errors.DockerException:
            self.client = None
    
    async def get_containers(self) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        
        try:
            containers = self.client.containers.list(all=True)
            result = []
            
            for container in containers:
                container_info = {
                    "id": container.id[:12],
                    "name": container.name,
                    "image": container.image.tags[0] if container.image.tags else "Unknown",
                    "status": container.status,
                    "created": container.attrs["Created"],
                    "ports": self._get_ports(container),
                }
                
                # Get stats for running containers
                if container.status == "running":
                    try:
                        stats = container.stats(stream=False)
                        container_info["stats"] = self._calculate_stats(stats)
                    except Exception:
                        container_info["stats"] = None
                
                result.append(container_info)
            
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def _get_ports(self, container) -> List[str]:
        ports = []
        port_bindings = container.attrs.get("NetworkSettings", {}).get("Ports", {})
        for private_port, host_configs in port_bindings.items():
            if host_configs:
                for host_config in host_configs:
                    ports.append(f"{host_config['HostPort']}:{private_port}")
        return ports
    
    def _calculate_stats(self, stats: Dict) -> Dict[str, float]:
        # Calculate CPU percentage
        cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                   stats["precpu_stats"]["cpu_usage"]["total_usage"]
        system_cpu_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                          stats["precpu_stats"]["system_cpu_usage"]
        
        cpu_percent = 0
        if system_cpu_delta > 0:
            cpu_percent = (cpu_delta / system_cpu_delta) * \
                         len(stats["cpu_stats"]["cpu_usage"]["percpu_usage"]) * 100
        
        # Calculate memory percentage
        memory_usage = stats["memory_stats"].get("usage", 0)
        memory_limit = stats["memory_stats"].get("limit", 1)
        memory_percent = (memory_usage / memory_limit) * 100
        
        return {
            "cpu_percent": round(cpu_percent, 2),
            "memory_percent": round(memory_percent, 2),
            "memory_usage_mb": round(memory_usage / 1024 / 1024, 2)
        }

docker_manager = DockerManager()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Docker Dashboard</title>
        <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100">
        <div id="app" class="container mx-auto p-8">
            <h1 class="text-3xl font-bold mb-6">🐳 Docker Dashboard</h1>
            
            <div class="grid grid-cols-4 gap-4 mb-8">
                <div class="bg-white p-6 rounded-lg shadow">
                    <h3 class="text-lg font-semibold">Total</h3>
                    <p class="text-2xl font-bold">{{ containers.length }}</p>
                </div>
                <div class="bg-white p-6 rounded-lg shadow">
                    <h3 class="text-lg font-semibold">Running</h3>
                    <p class="text-2xl font-bold text-green-600">{{ runningCount }}</p>
                </div>
                <div class="bg-white p-6 rounded-lg shadow">
                    <h3 class="text-lg font-semibold">Stopped</h3>
                    <p class="text-2xl font-bold text-red-600">{{ stoppedCount }}</p>
                </div>
                <div class="bg-white p-6 rounded-lg shadow">
                    <button @click="refreshData" class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
                        Refresh
                    </button>
                </div>
            </div>
            
            <div class="bg-white rounded-lg shadow overflow-hidden">
                <table class="min-w-full">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left">Name</th>
                            <th class="px-6 py-3 text-left">Image</th>
                            <th class="px-6 py-3 text-left">Status</th>
                            <th class="px-6 py-3 text-left">CPU %</th>
                            <th class="px-6 py-3 text-left">Memory %</th>
                            <th class="px-6 py-3 text-left">Ports</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="container in containers" :key="container.id" class="border-t">
                            <td class="px-6 py-4">{{ container.name }}</td>
                            <td class="px-6 py-4">{{ container.image }}</td>
                            <td class="px-6 py-4">
                                <span :class="statusClass(container.status)" class="px-2 py-1 rounded text-sm">
                                    {{ container.status }}
                                </span>
                            </td>
                            <td class="px-6 py-4">
                                {{ container.stats ? container.stats.cpu_percent + '%' : 'N/A' }}
                            </td>
                            <td class="px-6 py-4">
                                {{ container.stats ? container.stats.memory_percent.toFixed(1) + '%' : 'N/A' }}
                            </td>
                            <td class="px-6 py-4">{{ container.ports.join(', ') || 'None' }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <script>
        const { createApp } = Vue;
        
        createApp({
            data() {
                return {
                    containers: []
                }
            },
            computed: {
                runningCount() {
                    return this.containers.filter(c => c.status === 'running').length;
                },
                stoppedCount() {
                    return this.containers.filter(c => c.status === 'exited').length;
                }
            },
            methods: {
                async refreshData() {
                    try {
                        const response = await fetch('/api/containers');
                        this.containers = await response.json();
                    } catch (error) {
                        console.error('Failed to fetch containers:', error);
                    }
                },
                statusClass(status) {
                    return status === 'running' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';
                }
            },
            async mounted() {
                await this.refreshData();
                setInterval(this.refreshData, 10000); // Refresh every 10 seconds
            }
        }).mount('#app');
        </script>
    </body>
    </html>
    """

@app.get("/api/containers")
async def get_containers():
    return await docker_manager.get_containers()

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "docker_available": docker_manager.client is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)