import psutil
import time

# Record the boot time when the module loads
BOOT_TIME = psutil.boot_time()

def get_system_metrics() -> dict:
    # CPU Usage
    cpu_percent = psutil.cpu_percent(interval=None)
    
    # Memory Usage
    memory = psutil.virtual_memory()
    ram_percent = memory.percent
    
    # Uptime in seconds
    uptime = time.time() - BOOT_TIME
    
    # Temperature (macOS and Windows don't support psutil.sensors_temperatures() out of the box, Linux/Pi does)
    temp = None
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            # Usually 'cpu_thermal' or 'coretemp' on Linux
            for name, entries in temps.items():
                if entries:
                    temp = entries[0].current
                    break
    except Exception:
        pass
        
    if temp is None:
        temp = 45.0 # Fallback mock value for development (macOS/Windows)
        
    # Estimated Power (Mock logic for now, could be based on CPU usage)
    # Pi 4 max power is roughly 6W-7W. Let's do a simple mock.
    power_w = 2.5 + (cpu_percent / 100.0) * 4.0
    
    return {
        "cpu_percent": round(cpu_percent, 1),
        "ram_percent": round(ram_percent, 1),
        "temperature": round(temp, 1),
        "uptime": int(uptime),
        "power_w": round(power_w, 2)
    }
