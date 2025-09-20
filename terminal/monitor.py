import psutil
import time

def get_system_info():
    """Get system information"""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        'cpu': cpu_percent,
        'memory': {
            'total': memory.total,
            'available': memory.available,
            'percent': memory.percent
        },
        'disk': {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent
        }
    }

def get_process_list(limit=10):
    """Get list of running processes"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_percent', 'cpu_percent']):
        try:
            pinfo = proc.info
            processes.append(pinfo)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    # Sort by memory usage and get top processes
    processes.sort(key=lambda x: x['memory_percent'], reverse=True)
    return processes[:limit]

def monitor_cmd(terminal, *args):
    """Display system monitoring information"""
    info = get_system_info()
    processes = get_process_list(5)
    
    result = [
        "System Monitor",
        "==============",
        f"CPU Usage: {info['cpu']}%",
        f"Memory: {info['memory']['percent']}% used ({info['memory']['available'] // (1024*1024)} MB available)",
        f"Disk: {info['disk']['percent']}% used ({info['disk']['free'] // (1024*1024*1024)} GB free)",
        "",
        "Top Processes:",
        "PID\tName\t\tMemory %\tCPU %"
    ]
    
    for proc in processes:
        result.append(f"{proc['pid']}\t{proc['name'][:15]}\t{proc['memory_percent']:.1f}%\t\t{proc['cpu_percent']:.1f}%")
    
    return "\n".join(result)