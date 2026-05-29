from html import escape
from pathlib import Path
from string import Template
from urllib.parse import parse_qs, quote

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from starlette.datastructures import UploadFile as StarletteUploadFile

from maskflow.api.dependencies import runtime_paths_dependency
from maskflow.core.directory import SUPPORTED_EXTENSIONS
from maskflow.plugins.builtin import build_builtin_plugin_registry
from maskflow.rules.loader import RulesLoader
from maskflow.runtime.paths import RuntimePaths
from maskflow.runtime.settings import get_settings
from maskflow.services.demasking import DemaskingService
from maskflow.services.file_jobs import FileMaskingJobService
from maskflow.services.text_masking import TextMaskingService
from maskflow.utils.logging import get_logger
from maskflow.web_htmx.config_summary import render_nlp_summary

router = APIRouter(tags=["web"])
logger = get_logger("maskflow.web")
_EXPECTED_WEB_ERRORS = (
    ValueError,
    FileNotFoundError,
    RuntimeError,
    ImportError,
    OSError,
)


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


def render_error(error: Exception, status_code: int) -> HTMLResponse:
    return HTMLResponse(
        f'<span class="error">{escape(str(error))}</span>',
        status_code=status_code,
    )


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    _ = request
    return render_template(
        "index.html",
        title="MaskFlow",
        active_index="active",
        active_jobs="",
        active_configs="",
        supported_extensions=", ".join(sorted(SUPPORTED_EXTENSIONS)),
    )


@router.post("/web/mask-text", response_class=HTMLResponse)
async def web_mask_text(request: Request) -> HTMLResponse:
    payload = parse_qs((await request.body()).decode("utf-8"))
    text = payload.get("text", [""])[0]

    if not text:
        return HTMLResponse('<span class="error">Text is required</span>', status_code=400)

    try:
        result = TextMaskingService().mask_text(
            text=text,
            config_path=get_settings().default_config,
        )
    except _EXPECTED_WEB_ERRORS as error:
        logger.warning(
            "web_mask_text_failed",
            error_type=type(error).__name__,
            error_message=str(error),
        )
        return render_error(error, status_code=400)

    return HTMLResponse(escape(result.masked_text))


@router.post("/web/demask-text", response_class=HTMLResponse)
async def web_demask_text(request: Request) -> HTMLResponse:
    payload = parse_qs((await request.body()).decode("utf-8"))
    text = payload.get("text", [""])[0]

    if not text:
        return HTMLResponse('<span class="error">Text is required</span>', status_code=400)

    try:
        demasked, _ = DemaskingService().demask_text(
            text=text,
            config_path=get_settings().default_config,
        )
    except _EXPECTED_WEB_ERRORS as error:
        logger.warning(
            "web_demask_text_failed",
            error_type=type(error).__name__,
            error_message=str(error),
        )
        return render_error(error, status_code=400)

    return HTMLResponse(escape(demasked))


@router.post("/web/mask-file", response_class=HTMLResponse)
async def web_mask_file(request: Request) -> HTMLResponse:
    form = await request.form()
    uploaded = form.get("file")

    if not isinstance(uploaded, StarletteUploadFile):
        return HTMLResponse('<span class="error">File is required</span>', status_code=400)

    service = FileMaskingJobService()

    try:
        source_path = service.save_upload(
            filename=uploaded.filename or "",
            stream=uploaded.file,
        )
        result = service.process_file(
            source_path=source_path,
            original_name=uploaded.filename or "",
            config_path=get_settings().default_config,
        )
    except _EXPECTED_WEB_ERRORS as error:
        logger.warning(
            "web_mask_file_failed",
            error_type=type(error).__name__,
            error_message=str(error),
        )
        return render_error(error, status_code=400)
    except Exception as error:
        logger.error(
            "web_mask_file_unexpected_error",
            error_type=type(error).__name__,
            error_message=str(error),
        )
        return render_error(error, status_code=500)

    output_name = escape(result.output_path.name)
    download_url = (
        f"/downloads/jobs/{quote(result.job_id)}/{quote(result.output_path.name)}"
    )
    report_url = f"/downloads/reports/{quote(result.report_path.name)}"

    return HTMLResponse(
        "\n".join(
            [
                '<div class="job-result">',
                f"<strong>{output_name}</strong>",
                "<dl>",
                f"<div><dt>Matches</dt><dd>{result.report.matches_applied}</dd></div>",
                f"<div><dt>Skipped</dt><dd>{result.report.matches_skipped}</dd></div>",
                "</dl>",
                f'<a class="button-link" href="{download_url}">Download Masked File</a>',
                f'<a class="secondary-link" href="{report_url}">Report JSON</a>',
                "</div>",
            ],
        )
    )


@router.post("/web/demask-file", response_class=HTMLResponse)
async def web_demask_file(request: Request) -> HTMLResponse:
    form = await request.form()
    uploaded = form.get("file")

    if not isinstance(uploaded, StarletteUploadFile):
        return HTMLResponse('<span class="error">File is required</span>', status_code=400)

    service = FileMaskingJobService()

    try:
        source_path = service.save_upload(
            filename=uploaded.filename or "",
            stream=uploaded.file,
        )
        result = service.demask_file(
            source_path=source_path,
            original_name=uploaded.filename or "",
            config_path=get_settings().default_config,
        )
    except _EXPECTED_WEB_ERRORS as error:
        logger.warning(
            "web_demask_file_failed",
            error_type=type(error).__name__,
            error_message=str(error),
        )
        return render_error(error, status_code=400)
    except Exception as error:
        logger.error(
            "web_demask_file_unexpected_error",
            error_type=type(error).__name__,
            error_message=str(error),
        )
        return render_error(error, status_code=500)

    output_name = escape(result.output_path.name)
    download_url = (
        f"/downloads/jobs/{quote(result.job_id)}/{quote(result.output_path.name)}"
    )

    return HTMLResponse(
        "\n".join(
            [
                '<div class="job-result">',
                f"<strong>{output_name}</strong>",
                "<dl>",
                f"<div><dt>Replacements</dt><dd>{result.replacements}</dd></div>",
                f"<div><dt>Mapping Size</dt><dd>{result.mapping_size}</dd></div>",
                "</dl>",
                f'<a class="button-link" href="{download_url}">Download Demasked File</a>',
                "</div>",
            ],
        )
    )


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
    nlp_config = RulesLoader.load(get_settings().default_config, validate_secret=False).nlp

    return render_template(
        "configs.html",
        title="Configs",
        active_index="",
        active_jobs="",
        active_configs="active",
        config_items=config_items or "<li>No runtime configs yet</li>",
        rule_items=rule_items,
        nlp_summary=render_nlp_summary(nlp_config),
    )
