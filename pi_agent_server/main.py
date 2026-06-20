from fastapi import FastAPI
import uvicorn
import logging
from mdns_broadcaster import MDNSBroadcaster
from hardware_metrics import get_system_metrics
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PORT = 8001
broadcaster = MDNSBroadcaster(port=PORT)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Pi Agent Server...")
    await broadcaster.start()
    yield
    # Shutdown
    logger.info("Shutting down Pi Agent Server...")
    await broadcaster.stop()

app = FastAPI(lifespan=lifespan)

from services import get_all_services, control_service, reboot_system
from pydantic import BaseModel
from fastapi import HTTPException

@app.get("/api/state")
async def read_state():
    """
    Return unified state containing both metrics and services.
    """
    return {
        "metrics": get_system_metrics(),
        "services": get_all_services()
    }

# Keep the old one for backwards compatibility during transition
@app.get("/api/metrics")
async def read_metrics():
    return get_system_metrics()

class ServiceAction(BaseModel):
    action: str

@app.post("/api/services/{service_id}")
async def manage_service(service_id: str, payload: ServiceAction):
    """
    Start or stop a specific service.
    """
    success = control_service(service_id, payload.action)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to execute action")
    return {"status": "success"}

@app.post("/api/system/reboot")
async def trigger_reboot():
    """
    Reboot the Raspberry Pi.
    """
    reboot_system()
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
