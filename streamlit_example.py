"""
Streamlit Docker Dashboard Example
Much simpler than Flask + HTML/JS
"""

import streamlit as st
import docker
import pandas as pd
import time
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Docker Dashboard",
    page_icon="🐳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("🐳 Docker Dashboard")

# Sidebar
with st.sidebar:
    st.header("Controls")
    auto_refresh = st.checkbox("Auto Refresh", value=True)
    refresh_interval = st.slider("Refresh Interval (seconds)", 5, 60, 10)
    
    if st.button("Refresh Now"):
        st.rerun()

# Main content
try:
    client = docker.from_env()
    containers = client.containers.list(all=True)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Containers", len(containers))
    
    with col2:
        running = len([c for c in containers if c.status == 'running'])
        st.metric("Running", running)
    
    with col3:
        stopped = len([c for c in containers if c.status == 'exited'])
        st.metric("Stopped", stopped)
    
    with col4:
        st.metric("Healthy", len([c for c in containers if 'health' in c.attrs.get('State', {}) and c.attrs['State']['Health']['Status'] == 'healthy']))
    
    # Container list
    st.header("Containers")
    
    if containers:
        # Create DataFrame
        container_data = []
        for container in containers:
            try:
                stats = container.stats(stream=False) if container.status == 'running' else None
                cpu_percent = 0
                memory_percent = 0
                
                if stats:
                    # Calculate CPU percentage
                    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                    system_cpu_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                    if system_cpu_delta > 0:
                        cpu_percent = (cpu_delta / system_cpu_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
                    
                    # Memory percentage
                    if 'memory_stats' in stats:
                        memory_usage = stats['memory_stats'].get('usage', 0)
                        memory_limit = stats['memory_stats'].get('limit', 1)
                        memory_percent = (memory_usage / memory_limit) * 100
                
                container_data.append({
                    'Name': container.name,
                    'Image': container.image.tags[0] if container.image.tags else 'Unknown',
                    'Status': container.status,
                    'CPU %': f"{cpu_percent:.1f}%" if cpu_percent else "N/A",
                    'Memory %': f"{memory_percent:.1f}%" if memory_percent else "N/A",
                    'Ports': ', '.join([f"{port['HostPort']}:{port['PrivatePort']}" for port in container.attrs['NetworkSettings']['Ports'].values() for port in port if port]) if container.attrs['NetworkSettings']['Ports'] else 'None'
                })
            except Exception as e:
                st.error(f"Error getting stats for {container.name}: {e}")
                continue
        
        df = pd.DataFrame(container_data)
        st.dataframe(df, use_container_width=True)
        
        # Container actions
        st.header("Container Actions")
        selected_container = st.selectbox("Select Container", [c.name for c in containers])
        
        col1, col2, col3 = st.columns(3)
        
        if selected_container:
            container = client.containers.get(selected_container)
            
            with col1:
                if st.button("Start") and container.status != 'running':
                    container.start()
                    st.success(f"Started {selected_container}")
                    st.rerun()
            
            with col2:
                if st.button("Stop") and container.status == 'running':
                    container.stop()
                    st.success(f"Stopped {selected_container}")
                    st.rerun()
            
            with col3:
                if st.button("Restart"):
                    container.restart()
                    st.success(f"Restarted {selected_container}")
                    st.rerun()
        
        # Logs section
        st.header("Container Logs")
        if selected_container:
            container = client.containers.get(selected_container)
            logs = container.logs(tail=50).decode('utf-8')
            st.text_area("Logs", logs, height=300)
    
    else:
        st.info("No containers found")

except docker.errors.DockerException as e:
    st.error(f"Docker connection failed: {e}")
    st.info("Make sure Docker is running and accessible")

# Auto refresh
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()