from html import escape
from pathlib import Path
from string import Template
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from maskflow.api.dependencies import runtime_paths_dependency
from maskflow.plugins.builtin import build_builtin_plugin_registry
from maskflow.runtime.paths import RuntimePaths
from maskflow.runtime.settings import get_settings
from maskflow.services.text_masking import TextMaskingService

router = APIRouter(tags=["web"])


def package_dir() -> Path:
    return Path(__file__).parent


def templates_dir() -> Path:
    return package_dir() / "templates"


def static_dir() -> Path:
    return package_dir() / "static"


def render_template(name: str, **context: str) -> HTMLResponse:
    base = Template((templates_dir() / "base.html").read_text(encoding="utf-8"))
    body = Template((templates_dir() / name).read_text(encoding="utf-8")).safe_substitute(
        context,
    )
    html = base.safe_substitute(
        {
            **context,
            "body": body,
        },
    )

    return HTMLResponse(html)


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    _ = request
    return render_template(
        "index.html",
        title="MaskFlow",
        active_index="active",
        active_jobs="",
        active_configs="",
    )


@router.post("/web/mask-text", response_class=HTMLResponse)
async def web_mask_text(request: Request) -> HTMLResponse:
    payload = parse_qs((await request.body()).decode("utf-8"))
    text = payload.get("text", [""])[0]

    if not text:
        return HTMLResponse('<span class="error">Text is required</span>', status_code=400)

    result = TextMaskingService().mask_text(
        text=text,
        config_path=get_settings().default_config,
    )

    return HTMLResponse(escape(result.masked_text))


@router.get("/jobs", response_class=HTMLResponse)
def jobs(request: Request, paths: RuntimePaths = Depends(runtime_paths_dependency)) -> HTMLResponse:
    _ = request
    report_items = "\n".join(
        f'<li><a href="/downloads/reports/{escape(path.name)}">{escape(path.name)}</a></li>'
        for path in sorted(paths.reports_dir.glob("*"))
        if path.is_file()
    )

    return render_template(
        "jobs.html",
        title="Jobs",
        active_index="",
        active_jobs="active",
        active_configs="",
        report_items=report_items or "<li>No reports yet</li>",
    )


@router.get("/configs", response_class=HTMLResponse)
def configs(
    request: Request,
    paths: RuntimePaths = Depends(runtime_paths_dependency),
) -> HTMLResponse:
    _ = request
    config_items = "\n".join(
        f"<li>{escape(path.name)}</li>"
        for path in sorted(paths.configs_dir.glob("*.yaml"))
        if path.is_file()
    )

    rules = build_builtin_plugin_registry()
    rule_items = "\n".join(f"<li>{escape(name)}</li>" for name in sorted(rules.all()))

    return render_template(
        "configs.html",
        title="Configs",
        active_index="",
        active_jobs="",
        active_configs="active",
        config_items=config_items or "<li>No runtime configs yet</li>",
        rule_items=rule_items,
    )
