"""VERITAS API entrypoint.

uvicorn imports this as `app.main:app` (docker-compose.yml `api` service).
Routers (auth, cases, evidence, graph) attach here in later weeks.
"""

from fastapi import FastAPI

from app.config import settings

app = FastAPI(title="VERITAS")

# --- Cross-cutting concerns to wire in as routes appear ---
# CORS middleware (dev defaults) once the frontend has an origin
# auth router (Week 2), case/evidence/graph routers (Weeks 2-5)


@app.get("/health")
def health() -> dict:
    """Liveness probe.

    Reports the deployment name from settings on purpose: if config loading
    is broken, this endpoint fails at boot instead of lying about health.
    """
    return {"status": "ok", "deployment": settings.deployment_name}
