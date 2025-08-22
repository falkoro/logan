"""
Streamlit Docker Dashboard
A modern, interactive Docker management interface
"""

import streamlit as st
import pandas as pd
import time
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Try to import docker, but continue without it for testing
try:
    import docker
    DOCKER_AVAILABLE = True
    try:
        docker_client = docker.from_env()
        docker_client.ping()
        DOCKER_CONNECTED = True
    except Exception:
        DOCKER_CONNECTED = False
        docker_client = None
except ImportError:
    DOCKER_AVAILABLE = False
    DOCKER_CONNECTED = False
    docker_client = None

# Page configuration
st.set_page_config(
    page_title="Docker Dashboard",
    page_icon="🐳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .status-running { color: #28a745; }
    .status-stopped { color: #dc3545; }
    .status-healthy { color: #28a745; }
    .status-unhealthy { color: #ffc107; }
    .container-name { font-weight: bold; font-size: 1.1em; }
</style>
""", unsafe_allow_html=True)

# Mock data for when Docker isn't available
MOCK_CONTAINERS = [
    {
        'name': 'plex-media-server',
        'image': 'plexinc/pms-docker:latest',
        'status': 'running',
        'created': datetime.now() - timedelta(days=7),
        'ports': ['32400:32400', '3005:3005'],
        'cpu_percent': 15.2,
        'memory_percent': 23.8,
        'memory_usage_mb': 512,
        'network_rx_mb': 1.5,
        'network_tx_mb': 2.3
    },
    {
        'name': 'sonarr',
        'image': 'linuxserver/sonarr:latest',
        'status': 'running',
        'created': datetime.now() - timedelta(days=8),
        'ports': ['8989:8989'],
        'cpu_percent': 5.8,
        'memory_percent': 12.4,
        'memory_usage_mb': 256,
        'network_rx_mb': 0.5,
        'network_tx_mb': 1.0
    },
    {
        'name': 'radarr',
        'image': 'linuxserver/radarr:latest',
        'status': 'running',
        'created': datetime.now() - timedelta(days=9),
        'ports': ['7878:7878'],
        'cpu_percent': 3.2,
        'memory_percent': 8.7,
        'memory_usage_mb': 128,
        'network_rx_mb': 0.3,
        'network_tx_mb': 0.5
    },
    {
        'name': 'nginx-proxy',
        'image': 'nginx:alpine',
        'status': 'exited',
        'created': datetime.now() - timedelta(days=12),
        'ports': [],
        'cpu_percent': 0,
        'memory_percent': 0,
        'memory_usage_mb': 0,
        'network_rx_mb': 0,
        'network_tx_mb': 0
    },
    {
        'name': 'redis-cache',
        'image': 'redis:7-alpine',
        'status': 'running',
        'created': datetime.now() - timedelta(days=11),
        'ports': ['6379:6379'],
        'cpu_percent': 1.5,
        'memory_percent': 4.2,
        'memory_usage_mb': 64,
        'network_rx_mb': 0.1,
        'network_tx_mb': 0.2
    }
]

def get_container_data():
    """Get container data from Docker or return mock data"""
    if DOCKER_CONNECTED and docker_client:
        try:
            containers = docker_client.containers.list(all=True)
            container_data = []
            
            for container in containers:
                # Basic container info
                data = {
                    'name': container.name,
                    'image': container.image.tags[0] if container.image.tags else 'Unknown',
                    'status': container.status,
                    'created': datetime.fromisoformat(container.attrs['Created'].replace('Z', '+00:00')),
                    'ports': get_container_ports(container),
                }
                
                # Get stats for running containers
                if container.status == 'running':
                    try:
                        stats = container.stats(stream=False)
                        stats_data = calculate_container_stats(stats)
                        data.update(stats_data)
                    except Exception as e:
                        st.warning(f"Failed to get stats for {container.name}: {e}")
                        data.update({
                            'cpu_percent': 0,
                            'memory_percent': 0,
                            'memory_usage_mb': 0,
                            'network_rx_mb': 0,
                            'network_tx_mb': 0
                        })
                else:
                    data.update({
                        'cpu_percent': 0,
                        'memory_percent': 0,
                        'memory_usage_mb': 0,
                        'network_rx_mb': 0,
                        'network_tx_mb': 0
                    })
                
                container_data.append(data)
            
            return container_data
            
        except Exception as e:
            st.error(f"Failed to get Docker data: {e}")
            return MOCK_CONTAINERS
    else:
        return MOCK_CONTAINERS

def get_container_ports(container):
    """Extract ports from container"""
    ports = []
    port_bindings = container.attrs.get('NetworkSettings', {}).get('Ports', {})
    for private_port, host_configs in port_bindings.items():
        if host_configs:
            for host_config in host_configs:
                ports.append(f"{host_config['HostPort']}:{private_port}")
    return ports

def calculate_container_stats(stats):
    """Calculate CPU and memory statistics"""
    # Calculate CPU percentage
    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
               stats['precpu_stats']['cpu_usage']['total_usage']
    system_cpu_delta = stats['cpu_stats']['system_cpu_usage'] - \
                      stats['precpu_stats']['system_cpu_usage']
    
    cpu_percent = 0
    if system_cpu_delta > 0:
        cpu_percent = (cpu_delta / system_cpu_delta) * \
                     len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
    
    # Calculate memory percentage
    memory_usage = stats['memory_stats'].get('usage', 0)
    memory_limit = stats['memory_stats'].get('limit', 1)
    memory_percent = (memory_usage / memory_limit) * 100
    
    # Network stats
    network_stats = stats.get('networks', {})
    total_rx = sum(net['rx_bytes'] for net in network_stats.values())
    total_tx = sum(net['tx_bytes'] for net in network_stats.values())
    
    return {
        'cpu_percent': round(cpu_percent, 2),
        'memory_percent': round(memory_percent, 2),
        'memory_usage_mb': round(memory_usage / 1024 / 1024, 1),
        'network_rx_mb': round(total_rx / 1024 / 1024, 2),
        'network_tx_mb': round(total_tx / 1024 / 1024, 2)
    }

def main():
    # Header
    st.title("🐳 Docker Dashboard")
    
    # Connection status
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        if DOCKER_CONNECTED:
            st.success("✅ Connected to Docker")
        elif DOCKER_AVAILABLE:
            st.warning("⚠️ Docker installed but not running")
        else:
            st.error("❌ Docker not available")
    
    with col2:
        if not DOCKER_CONNECTED:
            st.info("📊 Showing demo data")
    
    with col3:
        if st.button("🔄 Refresh", type="primary"):
            st.rerun()
    
    # Sidebar controls
    with st.sidebar:
        st.header("🎛️ Controls")
        
        # Auto refresh
        auto_refresh = st.checkbox("🔄 Auto Refresh", value=False)
        if auto_refresh:
            refresh_interval = st.slider("Refresh Interval (seconds)", 5, 60, 10)
        
        # Filter options
        st.subheader("🔍 Filters")
        status_filter = st.selectbox(
            "Status",
            ["All", "Running", "Stopped"],
            index=0
        )
        
        # Display options
        st.subheader("📊 Display")
        show_stats = st.checkbox("Show Statistics", value=True)
        show_charts = st.checkbox("Show Charts", value=True)
        
        # Container actions
        st.subheader("🚀 Quick Actions")
        if st.button("🛑 Stop All"):
            st.info("This would stop all running containers")
        if st.button("▶️ Start All"):
            st.info("This would start all stopped containers")
    
    # Get container data
    container_data = get_container_data()
    
    # Apply filters
    if status_filter == "Running":
        container_data = [c for c in container_data if c['status'] == 'running']
    elif status_filter == "Stopped":
        container_data = [c for c in container_data if c['status'] != 'running']
    
    # Overview metrics
    total_containers = len(container_data)
    running_containers = len([c for c in container_data if c['status'] == 'running'])
    stopped_containers = total_containers - running_containers
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📦 Total Containers", total_containers)
    
    with col2:
        st.metric("✅ Running", running_containers, delta=f"{running_containers}")
    
    with col3:
        st.metric("⛔ Stopped", stopped_containers, delta=f"-{stopped_containers}" if stopped_containers > 0 else "0")
    
    with col4:
        if container_data:
            avg_cpu = sum(c['cpu_percent'] for c in container_data if c['status'] == 'running') / max(running_containers, 1)
            st.metric("💻 Avg CPU %", f"{avg_cpu:.1f}%")
    
    # Container details
    if container_data:
        st.subheader("📋 Container Details")
        
        # Create DataFrame for better display
        df_data = []
        for container in container_data:
            df_data.append({
                'Name': container['name'],
                'Image': container['image'],
                'Status': container['status'],
                'CPU %': f"{container['cpu_percent']:.1f}%" if container['cpu_percent'] > 0 else "N/A",
                'Memory %': f"{container['memory_percent']:.1f}%" if container['memory_percent'] > 0 else "N/A",
                'Memory (MB)': container['memory_usage_mb'],
                'Ports': ', '.join(container['ports']) if container['ports'] else 'None',
                'Created': container['created'].strftime('%Y-%m-%d %H:%M')
            })
        
        df = pd.DataFrame(df_data)
        
        # Style the dataframe
        def style_status(val):
            color = '#28a745' if val == 'running' else '#dc3545'
            return f'color: {color}; font-weight: bold'
        
        styled_df = df.style.applymap(style_status, subset=['Status'])
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        # Charts section
        if show_charts and running_containers > 0:
            st.subheader("📈 Resource Usage Charts")
            
            # Filter running containers for charts
            running_data = [c for c in container_data if c['status'] == 'running']
            
            if running_data:
                col1, col2 = st.columns(2)
                
                with col1:
                    # CPU usage chart
                    cpu_data = pd.DataFrame([
                        {'Container': c['name'], 'CPU %': c['cpu_percent']}
                        for c in running_data
                    ])
                    
                    fig_cpu = px.bar(
                        cpu_data, 
                        x='Container', 
                        y='CPU %',
                        title='CPU Usage by Container',
                        color='CPU %',
                        color_continuous_scale='Viridis'
                    )
                    fig_cpu.update_layout(height=400)
                    st.plotly_chart(fig_cpu, use_container_width=True)
                
                with col2:
                    # Memory usage chart
                    memory_data = pd.DataFrame([
                        {'Container': c['name'], 'Memory %': c['memory_percent']}
                        for c in running_data
                    ])
                    
                    fig_memory = px.bar(
                        memory_data,
                        x='Container',
                        y='Memory %',
                        title='Memory Usage by Container',
                        color='Memory %',
                        color_continuous_scale='Plasma'
                    )
                    fig_memory.update_layout(height=400)
                    st.plotly_chart(fig_memory, use_container_width=True)
                
                # Network usage chart
                if any(c['network_rx_mb'] > 0 or c['network_tx_mb'] > 0 for c in running_data):
                    st.subheader("🌐 Network Usage")
                    
                    network_data = []
                    for c in running_data:
                        network_data.extend([
                            {'Container': c['name'], 'Direction': 'Received', 'MB': c['network_rx_mb']},
                            {'Container': c['name'], 'Direction': 'Transmitted', 'MB': c['network_tx_mb']}
                        ])
                    
                    network_df = pd.DataFrame(network_data)
                    fig_network = px.bar(
                        network_df,
                        x='Container',
                        y='MB',
                        color='Direction',
                        title='Network Usage (MB)',
                        barmode='group'
                    )
                    fig_network.update_layout(height=400)
                    st.plotly_chart(fig_network, use_container_width=True)
    
    else:
        st.info("🔍 No containers found matching the current filters.")
        
        if not DOCKER_CONNECTED:
            st.markdown("""
            ### 🚀 Getting Started
            
            To see real Docker data:
            1. **Install Docker Desktop** or ensure Docker daemon is running
            2. **Start some containers** to see them in the dashboard
            3. **Refresh the page** to load real data
            
            Currently showing demo data for testing the interface.
            """)
    
    # Container management section
    if container_data and DOCKER_CONNECTED:
        st.subheader("🛠️ Container Management")
        
        # Select container for actions
        container_names = [c['name'] for c in container_data]
        selected_container = st.selectbox("Select Container for Actions", container_names)
        
        if selected_container:
            container = next(c for c in container_data if c['name'] == selected_container)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if container['status'] != 'running':
                    if st.button("▶️ Start"):
                        try:
                            docker_container = docker_client.containers.get(selected_container)
                            docker_container.start()
                            st.success(f"Started {selected_container}")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to start: {e}")
            
            with col2:
                if container['status'] == 'running':
                    if st.button("⏹️ Stop"):
                        try:
                            docker_container = docker_client.containers.get(selected_container)
                            docker_container.stop()
                            st.success(f"Stopped {selected_container}")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to stop: {e}")
            
            with col3:
                if st.button("🔄 Restart"):
                    try:
                        docker_container = docker_client.containers.get(selected_container)
                        docker_container.restart()
                        st.success(f"Restarted {selected_container}")
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to restart: {e}")
            
            with col4:
                if st.button("📋 Logs"):
                    try:
                        docker_container = docker_client.containers.get(selected_container)
                        logs = docker_container.logs(tail=50).decode('utf-8', errors='ignore')
                        st.text_area("Container Logs", logs, height=300)
                    except Exception as e:
                        st.error(f"Failed to get logs: {e}")
    
    # Auto refresh logic
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

if __name__ == "__main__":
    main()