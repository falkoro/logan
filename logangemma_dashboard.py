"""
LoganGemma Dashboard
Condensed Docker management interface optimized for 1080p and 4K displays
"""

import streamlit as st
import pandas as pd
import time
import webbrowser
from datetime import datetime, timedelta

# Try to import docker and connect to remote host
try:
    import docker
    import requests
    DOCKER_AVAILABLE = True
    
    # Configuration via environment variables (defaults to localhost for public use)
    import os
    REMOTE_HOST = os.getenv('DOCKER_HOST_NAME', 'localhost')
    REMOTE_USER = os.getenv('REMOTE_USER', 'user')
    GLANCES_HOST = os.getenv('GLANCES_HOST', 'localhost')
    GLANCES_PORT = int(os.getenv('GLANCES_PORT', '61208'))
    
    # Try local Docker first, then remote via SSH tunnel or direct connection
    docker_client = None
    DOCKER_CONNECTED = False
    
    try:
        # Try local Docker first
        docker_client = docker.from_env()
        docker_client.ping()
        DOCKER_CONNECTED = True
        CONNECTION_TYPE = "Local Docker"
    except Exception:
        try:
            # Try remote Docker via TCP (if configured)
            # You might need to configure Docker daemon to accept TCP connections
            docker_client = docker.DockerClient(base_url=f"tcp://{REMOTE_HOST}:2376")
            docker_client.ping()
            DOCKER_CONNECTED = True
            CONNECTION_TYPE = f"Remote Docker ({REMOTE_HOST})"
        except Exception:
            DOCKER_CONNECTED = False
            docker_client = None
            CONNECTION_TYPE = "No Docker Connection"
    
    # Test Glances API connection
    GLANCES_CONNECTED = False
    try:
        glances_url = f"http://{GLANCES_HOST}:{GLANCES_PORT}/api/4/status"
        response = requests.get(glances_url, timeout=5)
        if response.status_code == 200:
            GLANCES_CONNECTED = True
    except Exception:
        GLANCES_CONNECTED = False

except ImportError:
    DOCKER_AVAILABLE = False
    DOCKER_CONNECTED = False
    GLANCES_CONNECTED = False
    docker_client = None
    CONNECTION_TYPE = "Docker not installed"

# Page configuration for condensed layout
st.set_page_config(
    page_title="LoganGemma Dashboard",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for ultra-condensed layout
st.markdown("""
<style>
    /* Remove default padding and margins */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 100%;
    }
    
    /* Compact metrics */
    .metric-row {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 0.5rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }
    
    /* Container cards */
    .container-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Status indicators */
    .status-running { 
        color: #059669; 
        font-weight: bold;
        background: #d1fae5;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.85rem;
    }
    .status-stopped { 
        color: #dc2626; 
        font-weight: bold;
        background: #fee2e2;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.85rem;
    }
    
    /* Compact table */
    .dataframe {
        font-size: 0.85rem;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    /* Button styling */
    .stButton > button {
        height: 2rem;
        font-size: 0.8rem;
        padding: 0.25rem 0.5rem;
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
</style>
""", unsafe_allow_html=True)

def get_system_info():
    """Get system information from Glances API"""
    if not GLANCES_CONNECTED:
        return None
    
    try:
        base_url = f"http://{GLANCES_HOST}:{GLANCES_PORT}/api/4"
        
        # Get various system metrics
        cpu_response = requests.get(f"{base_url}/cpu", timeout=3)
        memory_response = requests.get(f"{base_url}/mem", timeout=3)
        uptime_response = requests.get(f"{base_url}/uptime", timeout=3)
        
        system_info = {}
        
        if cpu_response.status_code == 200:
            cpu_data = cpu_response.json()
            system_info['cpu_percent'] = cpu_data.get('total', 0)
        
        if memory_response.status_code == 200:
            memory_data = memory_response.json()
            system_info['memory_percent'] = memory_data.get('percent', 0)
            system_info['memory_used_gb'] = round(memory_data.get('used', 0) / 1024 / 1024 / 1024, 1)
            system_info['memory_total_gb'] = round(memory_data.get('total', 0) / 1024 / 1024 / 1024, 1)
        
        if uptime_response.status_code == 200:
            uptime_data = uptime_response.json()
            uptime_seconds = uptime_data.get('uptime', 0) if isinstance(uptime_data, dict) else uptime_data
            days = uptime_seconds // 86400
            hours = (uptime_seconds % 86400) // 3600
            system_info['uptime'] = f"{days}d {hours}h"
        
        return system_info
        
    except Exception as e:
        st.warning(f"Failed to get system info: {e}")
        return None

def get_container_data():
    """Get container data from Docker"""
    if not DOCKER_CONNECTED or not docker_client:
        return []
    
    try:
        containers = docker_client.containers.list(all=True)
        container_data = []
        
        for container in containers:
            # Basic container info
            data = {
                'id': container.id[:12],
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
                except Exception:
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
        return []

def get_container_ports(container):
    """Extract ports from container with URLs"""
    ports = []
    port_bindings = container.attrs.get('NetworkSettings', {}).get('Ports', {})
    for private_port, host_configs in port_bindings.items():
        if host_configs:
            for host_config in host_configs:
                host_port = host_config['HostPort']
                ports.append({
                    'display': f"{host_port}:{private_port}",
                    'host_port': host_port,
                    'url': f"http://localhost:{host_port}"
                })
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
        'cpu_percent': round(cpu_percent, 1),
        'memory_percent': round(memory_percent, 1),
        'memory_usage_mb': round(memory_usage / 1024 / 1024, 0),
        'network_rx_mb': round(total_rx / 1024 / 1024, 1),
        'network_tx_mb': round(total_tx / 1024 / 1024, 1)
    }

def container_action_buttons(container_name, status):
    """Create action buttons for a container"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if status != 'running':
            if st.button("▶️", key=f"start_{container_name}", help="Start"):
                try:
                    docker_container = docker_client.containers.get(container_name)
                    docker_container.start()
                    st.success(f"Started {container_name}")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to start: {e}")
        else:
            st.write("✅")
    
    with col2:
        if status == 'running':
            if st.button("⏹️", key=f"stop_{container_name}", help="Stop"):
                try:
                    docker_container = docker_client.containers.get(container_name)
                    docker_container.stop()
                    st.success(f"Stopped {container_name}")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to stop: {e}")
        else:
            st.write("⏹️")
    
    with col3:
        if st.button("🔄", key=f"restart_{container_name}", help="Restart"):
            try:
                docker_container = docker_client.containers.get(container_name)
                docker_container.restart()
                st.success(f"Restarted {container_name}")
                time.sleep(2)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to restart: {e}")

def main():
    # Header with connection status
    connection_status = f"{CONNECTION_TYPE}"
    if GLANCES_CONNECTED:
        connection_status += f" | Glances ({GLANCES_HOST})"
    
    st.markdown(f"""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2rem;">💎 LoganGemma Dashboard</h1>
        <p style="margin: 0; opacity: 0.9;">Docker Container Management Hub</p>
        <p style="margin: 0; opacity: 0.8; font-size: 0.9rem;">{connection_status}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick controls row
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
    
    with col1:
        if DOCKER_CONNECTED:
            st.success("🐳 Docker Connected")
        else:
            st.error("❌ Docker Offline")
    
    with col2:
        if st.button("🔄 Refresh All", use_container_width=True):
            st.rerun()
    
    with col3:
        auto_refresh = st.checkbox("🔁 Auto (30s)")
    
    with col4:
        if st.button("🛑 Stop All", use_container_width=True):
            if DOCKER_CONNECTED:
                running_containers = [c for c in docker_client.containers.list() if c.status == 'running']
                for container in running_containers:
                    container.stop()
                st.success("Stopped all containers")
                st.rerun()
    
    with col5:
        if st.button("▶️ Start All", use_container_width=True):
            if DOCKER_CONNECTED:
                stopped_containers = [c for c in docker_client.containers.list(all=True) if c.status != 'running']
                for container in stopped_containers:
                    container.start()
                st.success("Started all containers")
                st.rerun()
    
    # Get container data
    container_data = get_container_data()
    
    if not container_data and DOCKER_CONNECTED:
        st.info("🔍 No containers found. Create some containers to see them here.")
        return
    elif not DOCKER_CONNECTED:
        st.warning("⚠️ Please start Docker to see containers")
        return
    
    # Get system info
    system_info = get_system_info()
    
    # Quick stats - Container info
    total_containers = len(container_data)
    running_containers = len([c for c in container_data if c['status'] == 'running'])
    stopped_containers = total_containers - running_containers
    total_cpu = sum(c['cpu_percent'] for c in container_data if c['status'] == 'running')
    total_memory_mb = sum(c['memory_usage_mb'] for c in container_data if c['status'] == 'running')
    
    # Stats row 1 - Container Overview
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📦 Containers", total_containers)
    with col2:
        st.metric("✅ Running", running_containers)
    with col3:
        st.metric("⛔ Stopped", stopped_containers)
    with col4:
        st.metric("💻 Cont CPU%", f"{total_cpu:.1f}")
    with col5:
        st.metric("🧠 Cont RAM MB", f"{total_memory_mb:.0f}")
    
    # Stats row 2 - System Overview (if Glances is connected)
    if system_info:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("🖥️ Host CPU%", f"{system_info.get('cpu_percent', 0):.1f}")
        with col2:
            st.metric("📊 Host RAM%", f"{system_info.get('memory_percent', 0):.1f}")
        with col3:
            st.metric("💾 Host RAM GB", f"{system_info.get('memory_used_gb', 0):.1f}/{system_info.get('memory_total_gb', 0):.1f}")
        with col4:
            st.metric("⏰ Uptime", system_info.get('uptime', 'N/A'))
        with col5:
            st.metric("🌐 Host", GLANCES_HOST)
    
    # Container grid - optimized for screen real estate
    st.subheader("🐳 Container Overview")
    
    # Create a more compact table
    table_data = []
    for container in container_data:
        # Status with color
        status_display = container['status'].title()
        if container['status'] == 'running':
            status_html = f'<span class="status-running">{status_display}</span>'
        else:
            status_html = f'<span class="status-stopped">{status_display}</span>'
        
        # Port buttons
        port_buttons = ""
        if container['ports']:
            for port_info in container['ports'][:3]:  # Limit to 3 ports
                port_buttons += f"""
                <a href="{port_info['url']}" target="_blank" 
                   style="background: #3b82f6; color: white; padding: 2px 6px; 
                          border-radius: 4px; text-decoration: none; margin-right: 4px; 
                          font-size: 0.8rem;">
                   {port_info['host_port']}
                </a>
                """
        
        table_data.append({
            'Container': container['name'],
            'Image': container['image'].split(':')[0],  # Remove tag for space
            'Status': status_html,
            'CPU%': f"{container['cpu_percent']:.1f}" if container['cpu_percent'] > 0 else "-",
            'RAM%': f"{container['memory_percent']:.1f}" if container['memory_percent'] > 0 else "-",
            'RAM MB': f"{container['memory_usage_mb']:.0f}" if container['memory_usage_mb'] > 0 else "-",
            'Net ↓MB': f"{container['network_rx_mb']:.1f}" if container['network_rx_mb'] > 0 else "-",
            'Net ↑MB': f"{container['network_tx_mb']:.1f}" if container['network_tx_mb'] > 0 else "-",
            'Ports': port_buttons,
            'ID': container['id']
        })
    
    # Display as HTML table for better control
    if table_data:
        # Create container action grid
        for i, container in enumerate(container_data):
            with st.container():
                col1, col2, col3, col4, col5, col6, col7, col8, col9, col10 = st.columns([2, 2, 1, 0.8, 0.8, 0.8, 0.8, 0.8, 2, 1])
                
                with col1:
                    st.write(f"**{container['name']}**")
                
                with col2:
                    st.write(container['image'].split(':')[0])
                
                with col3:
                    if container['status'] == 'running':
                        st.markdown('<span class="status-running">Running</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="status-stopped">Stopped</span>', unsafe_allow_html=True)
                
                with col4:
                    st.write(f"{container['cpu_percent']:.1f}%" if container['cpu_percent'] > 0 else "-")
                
                with col5:
                    st.write(f"{container['memory_percent']:.1f}%" if container['memory_percent'] > 0 else "-")
                
                with col6:
                    st.write(f"{container['memory_usage_mb']:.0f}" if container['memory_usage_mb'] > 0 else "-")
                
                with col7:
                    st.write(f"{container['network_rx_mb']:.1f}" if container['network_rx_mb'] > 0 else "-")
                
                with col8:
                    st.write(f"{container['network_tx_mb']:.1f}" if container['network_tx_mb'] > 0 else "-")
                
                with col9:
                    # Port access buttons
                    if container['ports']:
                        port_cols = st.columns(len(container['ports'][:4]))  # Max 4 ports
                        for j, port_info in enumerate(container['ports'][:4]):
                            with port_cols[j]:
                                if st.button(f"🌐 {port_info['host_port']}", 
                                           key=f"port_{container['name']}_{j}",
                                           help=f"Open {port_info['url']}"):
                                    webbrowser.open(port_info['url'])
                
                with col10:
                    # Action buttons
                    if DOCKER_CONNECTED:
                        action_cols = st.columns(3)
                        with action_cols[0]:
                            if container['status'] != 'running':
                                if st.button("▶️", key=f"start_{container['name']}", help="Start"):
                                    try:
                                        docker_container = docker_client.containers.get(container['name'])
                                        docker_container.start()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                        
                        with action_cols[1]:
                            if container['status'] == 'running':
                                if st.button("⏹️", key=f"stop_{container['name']}", help="Stop"):
                                    try:
                                        docker_container = docker_client.containers.get(container['name'])
                                        docker_container.stop()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                        
                        with action_cols[2]:
                            if st.button("🔄", key=f"restart_{container['name']}", help="Restart"):
                                try:
                                    docker_container = docker_client.containers.get(container['name'])
                                    docker_container.restart()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                
                st.divider()
    
    # Header row for table
    col1, col2, col3, col4, col5, col6, col7, col8, col9, col10 = st.columns([2, 2, 1, 0.8, 0.8, 0.8, 0.8, 0.8, 2, 1])
    st.markdown("---")
    with col1:
        st.write("**Container**")
    with col2:
        st.write("**Image**")
    with col3:
        st.write("**Status**")
    with col4:
        st.write("**CPU%**")
    with col5:
        st.write("**RAM%**")
    with col6:
        st.write("**RAM MB**")
    with col7:
        st.write("**↓ MB**")
    with col8:
        st.write("**↑ MB**")
    with col9:
        st.write("**Access Ports**")
    with col10:
        st.write("**Actions**")
    
    st.markdown("---")
    
    # Auto refresh
    if auto_refresh:
        time.sleep(30)
        st.rerun()

if __name__ == "__main__":
    main()