import subprocess
import json
import logging

logger = logging.getLogger(__name__)

# Native systemd services we want to monitor and control
MONITORED_SERVICES = ["ssh", "tailscaled"]

def get_docker_containers() -> list:
    """Fetch all docker containers and their status."""
    containers = []
    try:
        # Get all containers (running and stopped)
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{json .}}"],
            capture_output=True, text=True, check=True
        )
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            try:
                data = json.loads(line)
                name = data.get("Names", "")
                state_raw = data.get("State", "").lower()
                
                # Standardize state to 'running' or 'stopped'
                state = "running" if state_raw == "running" else "stopped"
                
                containers.append({
                    "id": f"docker_{name}",
                    "name": name,
                    "type": "docker",
                    "state": state
                })
            except json.JSONDecodeError:
                pass
    except Exception as e:
        logger.warning(f"Could not fetch docker containers: {e}")
    return containers

def get_system_services() -> list:
    """Fetch status of predefined systemd services."""
    services = []
    for srv in MONITORED_SERVICES:
        try:
            result = subprocess.run(
                ["systemctl", "is-active", srv],
                capture_output=True, text=True
            )
            state = "running" if result.stdout.strip() == "active" else "stopped"
            services.append({
                "id": f"system_{srv}",
                "name": srv,
                "type": "system",
                "state": state
            })
        except Exception as e:
            logger.warning(f"Could not fetch system service {srv}: {e}")
    return services

import os

MOUNT_BASE = "/mnt/pi_usb"

def get_usb_drives() -> list:
    """Fetch all removable or non-system USB partitions."""
    drives = []
    try:
        result = subprocess.run(
            ["lsblk", "-J", "-l", "-o", "KNAME,LABEL,MOUNTPOINT,SIZE,TYPE"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(result.stdout)
        
        system_mounts = ["/", "/boot/firmware", "[SWAP]"]
        
        active_knames = set()
        
        for dev in data.get("blockdevices", []):
            if dev.get("type") != "part":
                continue
                
            mountpoint = dev.get("mountpoint")
            if mountpoint in system_mounts:
                continue
                
            kname = dev.get("kname")
            if not kname.startswith("sd"):
                continue
                
            active_knames.add(kname)
            label = dev.get("label") or kname
            size = dev.get("size")
            state = "running" if mountpoint else "stopped"
            
            drives.append({
                "id": f"usb_{kname}",
                "name": f"{label} ({size})",
                "type": "usb",
                "state": state
            })
            
        # Auto-cleanup ghost directories
        if os.path.exists(MOUNT_BASE):
            for item in os.listdir(MOUNT_BASE):
                if item not in active_knames:
                    ghost_path = os.path.join(MOUNT_BASE, item)
                    try:
                        # rmdir only removes empty directories, so it's safe
                        subprocess.run(["sudo", "rmdir", ghost_path], capture_output=True)
                    except Exception:
                        pass
    except Exception as e:
        logger.error(f"Error fetching USB drives: {e}")
        
    return drives

def get_all_services() -> list:
    """Return a combined list of all controllable services."""
    return get_docker_containers() + get_system_services() + get_usb_drives()

def control_service(service_id: str, action: str) -> bool:
    """
    Start or stop a service based on its ID.
    Action must be 'start' or 'stop'.
    """
    if action not in ["start", "stop"]:
        return False
        
    try:
        if service_id.startswith("docker_"):
            name = service_id[len("docker_"):]
            subprocess.run(["docker", action, name], check=True)
            return True
        elif service_id.startswith("system_"):
            name = service_id[len("system_"):]
            subprocess.run(["sudo", "systemctl", action, name], check=True)
            return True
        elif service_id.startswith("usb_"):
            kname = service_id[len("usb_"):]
            device_path = f"/dev/{kname}"
            mountpoint = f"{MOUNT_BASE}/{kname}"
            
            if action == "start":
                subprocess.run(["sudo", "mkdir", "-p", mountpoint], check=True)
                subprocess.run(["sudo", "mount", device_path, mountpoint], check=True)
                return True
            elif action == "stop":
                subprocess.run(["sudo", "umount", device_path], check=True)
                return True
    except Exception as e:
        logger.error(f"Failed to {action} service {service_id}: {e}")
        return False
    return False

def reboot_system():
    """Trigger a system reboot."""
    subprocess.run(["sudo", "reboot"])
