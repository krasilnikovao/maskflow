from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from maskflow.api.routers import configs, downloads, health, jobs, rules
from maskflow.web_htmx.routes import router as web_router
from maskflow.web_htmx.routes import static_dir


def create_app(include_web: bool = False) -> FastAPI:
    app = FastAPI(
        title="MaskFlow API",
        version="0.1.0",
    )

    app.include_router(health.router)
    app.include_router(jobs.router)
    app.include_router(configs.router)
    app.include_router(rules.router)
    app.include_router(downloads.router)

    if include_web:
        app.mount(
            "/static",
            StaticFiles(directory=static_dir()),
            name="static",
        )
        app.include_router(web_router)

    return app
