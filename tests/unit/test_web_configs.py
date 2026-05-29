from maskflow.rules.models import NlpConfig
from maskflow.web_htmx.config_summary import render_nlp_summary


def test_render_nlp_summary_includes_provider_models() -> None:
    summary = render_nlp_summary(NlpConfig())

    assert "GLiNER" in summary
    assert "urchade/gliner_multi-v2.1" in summary
    assert "missing" in summary
    assert "Qwen/Qwen2.5-Coder-7B-Instruct" in summary
    assert "Auto download" in summary
