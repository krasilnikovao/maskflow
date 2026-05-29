from html import escape

from maskflow.nlp.status import collect_nlp_model_status
from maskflow.rules.models import NlpConfig


def render_nlp_summary(config: NlpConfig) -> str:
    status_by_provider = {
        status.provider: status
        for status in collect_nlp_model_status(config)
    }
    rows = [
        ("Enabled", str(config.enabled).lower()),
        ("Auto download", str(config.auto_download).lower()),
        ("Provider order", ", ".join(config.provider_order)),
        (
            "GLiNER",
            _provider_state(
                config.providers.gliner.enabled,
                config.providers.gliner.model_name,
                status_by_provider["gliner"].available,
            ),
        ),
        (
            "spaCy",
            _provider_state(
                config.providers.spacy.enabled,
                config.providers.spacy.model_name,
                status_by_provider["spacy"].available,
            ),
        ),
        ("Natasha", "enabled" if config.providers.natasha.enabled else "disabled"),
        (
            "Qwen",
            _provider_state(
                config.providers.qwen.enabled,
                config.providers.qwen.model_name,
                status_by_provider["qwen"].available,
            ),
        ),
    ]
    items = "\n".join(
        f"<div><dt>{escape(label)}</dt><dd>{escape(value)}</dd></div>"
        for label, value in rows
    )
    return f"<dl>{items}</dl>"


def _provider_state(enabled: bool, model_name: str, available: bool) -> str:
    state = "enabled" if enabled else "disabled"
    availability = "local" if available else "missing"
    return f"{state} / {model_name} / {availability}"
