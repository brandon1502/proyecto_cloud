#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mock Workers API for VM Placement lab.

- Runs a FastAPI server with uvicorn.
- Endpoint:
    GET http://<IP>:8081/api/v1/workers

Returns a hardcoded JSON with the list of workers
distribuidos en varias Availability Zones (AZ1, AZ2, AZ3).
"""

from typing import Dict, Any
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Mock Workers API")


def get_mock_workers() -> Dict[str, Any]:
    """
    Returns the hardcoded workers JSON.
    """
    return {
        "workers": [
            # =========================
            #   AZ1
            # =========================
            {
                "id": "worker-1",
                "name": "compute-node-1",
                "platform": "linux",
                "zone": "AZ1",
                "cpu_capacity": 15,
                "ram_gb_capacity": 128.0,
                "disk_gb_capacity": 1000.0,
                "current_usage": {
                    "cpu": {"mean": 14.0, "std": 2.3},
                    "ram_gb": {"mean": 64.0, "std": 8.5},
                    "disk_gb_used": 450.0
                },
                "enabled": True,
                "in_maintenance": False,
                "metadata": {"rack": "A1", "datacenter": "Lima"}
            },
            {
                "id": "worker-2",
                "name": "compute-node-2",
                "platform": "linux",
                "zone": "AZ1",
                "cpu_capacity": 16,
                "ram_gb_capacity": 256.0,
                "disk_gb_capacity": 2000.0,
                "current_usage": {
                    "cpu": {"mean": 13.5, "std": 1.5},
                    "ram_gb": {"mean": 32.0, "std": 4.0},
                    "disk_gb_used": 200.0
                },
                "enabled": True,
                "in_maintenance": False,
                "metadata": {"rack": "A2", "datacenter": "Lima"}
            },

            # =========================
            #   AZ2
            # =========================
            {
                "id": "worker-3",
                "name": "compute-node-3",
                "platform": "linux",
                "zone": "AZ2",
                "cpu_capacity": 24,
                "ram_gb_capacity": 64.0,
                "disk_gb_capacity": 1500.0,
                "current_usage": {
                    "cpu": {"mean": 10.0, "std": 2.0},
                    "ram_gb": {"mean": 40.0, "std": 6.0},
                    "disk_gb_used": 300.0
                },
                "enabled": True,
                "in_maintenance": False,
                "metadata": {"rack": "B1", "datacenter": "Arequipa"}
            },
            {
                "id": "worker-4",
                "name": "compute-node-4",
                "platform": "openstack",
                "zone": "AZ2",
                "cpu_capacity": 48,
                "ram_gb_capacity": 128.0,
                "disk_gb_capacity": 2500.0,
                "current_usage": {
                    "cpu": {"mean": 20.0, "std": 3.0},
                    "ram_gb": {"mean": 70.0, "std": 9.0},
                    "disk_gb_used": 800.0
                },
                "enabled": True,
                "in_maintenance": False,
                "metadata": {"rack": "B2", "datacenter": "Arequipa"}
            },

            # =========================
            #   AZ3
            # =========================
            {
                "id": "worker-5",
                "name": "compute-node-5",
                "platform": "openstack",
                "zone": "AZ3",
                "cpu_capacity": 16,
                "ram_gb_capacity": 32.0,
                "disk_gb_capacity": 800.0,
                "current_usage": {
                    "cpu": {"mean": 6.0, "std": 1.2},
                    "ram_gb": {"mean": 18.0, "std": 3.0},
                    "disk_gb_used": 150.0
                },
                "enabled": True,
                "in_maintenance": False,
                "metadata": {"rack": "C1", "datacenter": "Cusco"}
            },
            {
                "id": "worker-6",
                "name": "compute-node-6",
                "platform": "linux",
                "zone": "AZ3",
                "cpu_capacity": 32,
                "ram_gb_capacity": 64.0,
                "disk_gb_capacity": 1200.0,
                "current_usage": {
                    "cpu": {"mean": 25.0, "std": 4.0},
                    "ram_gb": {"mean": 50.0, "std": 7.0},
                    "disk_gb_used": 700.0
                },
                "enabled": True,
                "in_maintenance": False,
                "metadata": {"rack": "C2", "datacenter": "Cusco"}
            }
        ]
    }


@app.get("/api/v1/workers")
def list_workers() -> Dict[str, Any]:
    """
    Test endpoint:

      GET /api/v1/workers
      (any query params are ignored)

    Always returns the same hardcoded JSON with workers
    from zones AZ1, AZ2 and AZ3.
    """
    return get_mock_workers()


if __name__ == "__main__":
    # Run with: python3 workers_api.py
    uvicorn.run("workers_api:app", host="0.0.0.0", port=8081, reload=True)

