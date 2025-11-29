"""
Resources API Microservice
API para gestionar recursos del orquestador (VLANs, puertos VNC, etc.)
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .routes import vlans, vnc_ports, slices, vms, cleanup
from .database import get_db

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events"""
    logger.info("🚀 Starting Resources API Microservice...")
    yield
    logger.info("🛑 Shutting down Resources API Microservice...")


app = FastAPI(
    title="Resources API",
    description="API para gestionar recursos del orquestador (VLANs, puertos VNC, Slices y VMs)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(vlans.router, prefix="/api/v1/vlans", tags=["VLANs"])
app.include_router(vnc_ports.router, prefix="/api/v1/vnc-ports", tags=["VNC Ports"])
app.include_router(slices.router, prefix="/api/v1/slices", tags=["Slices"])
app.include_router(vms.router, prefix="/api/v1/vms", tags=["VMs"])
app.include_router(cleanup.router, prefix="/api/v1/cleanup", tags=["Cleanup"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Resources API",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check detallado"""
    return {
        "status": "healthy",
        "database": "connected"
    }
