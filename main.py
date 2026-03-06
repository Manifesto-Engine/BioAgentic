"""Sovereign Organism — Starter Kit.

The minimal entry point. Boots the organism on server start,
kills it on shutdown. That's it.
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from organism import Organism
from cortex_api import router as cortex_router, set_organism as set_cortex_organism
from pipeline_engine import router as engine_router, set_organism as set_engine_organism

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)

# ── The Organism ─────────────────────────────────────────
_organism = Organism()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """The organism is born when the server starts, dies when it stops."""
    # Wire organism to API routes
    set_cortex_organism(_organism)
    set_engine_organism(_organism)

    # Birth
    await _organism.birth()
    yield
    # Death
    await _organism.death()


app = FastAPI(
    title="Sovereign Organism",
    description="A living AI agent runtime with persistent memory, "
                "autonomous reasoning, and evolutionary pipelines.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(cortex_router)
app.include_router(engine_router)


@app.get("/")
def root():
    """Health check."""
    return {
        "organism": "Sovereign Organism Starter Kit",
        "version": "1.0.0",
        "alive": _organism.vitals.alive,
        "docs": "/docs",
    }
