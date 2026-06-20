import socket
from zeroconf import ServiceInfo, Zeroconf
import logging
import uuid
import asyncio

logger = logging.getLogger(__name__)

class MDNSBroadcaster:
    def __init__(self, port: int):
        self.port = port
        self.zeroconf = None
        self.service_info = None
        
    async def start(self):
        self.zeroconf = Zeroconf()
        
        # Get hostname (This will be the default device name in HA)
        hostname = socket.gethostname()
        
        # Get IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
            
        # Get MAC address
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff)
                        for ele in range(0,8*6,8)][::-1])
            
        logger.info(f"Starting mDNS broadcast. Hostname: {hostname}, IP: {IP}:{self.port}, MAC: {mac}")
        
        # Type must match HA manifest.json 'zeroconf' entry
        service_type = "_pi-agent._tcp.local."
        service_name = f"{hostname}.{service_type}"
        
        # Additional properties to send to HA
        properties = {
            b'mac_address': mac.encode('utf-8'),
            b'version': b'1.0.0'
        }
        
        self.service_info = ServiceInfo(
            service_type,
            service_name,
            addresses=[socket.inet_aton(IP)],
            port=self.port,
            properties=properties,
            server=f"{hostname}.local.",
        )
        
        # Run blocking zeroconf registration in a thread pool to prevent asyncio deadlocks
        await asyncio.to_thread(self.zeroconf.register_service, self.service_info)
        logger.info("mDNS broadcast started successfully.")

    async def stop(self):
        if self.zeroconf and self.service_info:
            logger.info("Stopping mDNS broadcast...")
            await asyncio.to_thread(self.zeroconf.unregister_service, self.service_info)
            self.zeroconf.close()
            logger.info("mDNS broadcast stopped.")
