from maskflow.nlp.download import ensure_model_available
from maskflow.nlp.paths import resolve_model_path
from maskflow.nlp.pipeline import NlpPipeline
from maskflow.nlp.providers.base import NlpProvider
from maskflow.nlp.providers.gliner import GlinerProvider
from maskflow.nlp.providers.natasha import NatashaProvider
from maskflow.nlp.providers.qwen import QwenProvider
from maskflow.nlp.providers.spacy import SpacyProvider
from maskflow.nlp.resolver import NlpResolver
from maskflow.rules.models import NlpConfig, NlpProviderName


def build_nlp_pipeline(config: NlpConfig) -> NlpPipeline | None:
    if not config.enabled:
        return None

    providers: list[NlpProvider] = []

    for provider_name in config.provider_order:
        provider = _build_provider(provider_name, config)
        if provider is not None:
            providers.append(provider)

    if not providers:
        raise ValueError("nlp.enabled is true but no NLP providers are enabled")

    return NlpPipeline(
        providers=providers,
        resolver=NlpResolver(min_confidence=config.min_confidence),
    )


def _build_provider(
    provider_name: NlpProviderName,
    config: NlpConfig,
) -> NlpProvider | None:
    if provider_name == "gliner":
        gliner_config = config.providers.gliner
        if not gliner_config.enabled:
            return None
        return GlinerProvider(
            model_name=gliner_config.model_name,
            model_path=ensure_model_available(
                provider="huggingface",
                model_name=gliner_config.model_name,
                model_path=(
                    resolve_model_path(gliner_config.model_path)
                    if gliner_config.model_path is not None
                    else None
                ),
                auto_download=_effective_auto_download(
                    config.auto_download,
                    gliner_config.auto_download,
                ),
            ),
            auto_download=_effective_auto_download(
                config.auto_download,
                gliner_config.auto_download,
            ),
            labels=gliner_config.labels,
            device=gliner_config.device,
            threshold=gliner_config.threshold,
            batch_size=gliner_config.batch_size,
        )

    if provider_name == "spacy":
        spacy_config = config.providers.spacy
        if not spacy_config.enabled:
            return None
        spacy_auto_download = _effective_auto_download(
            config.auto_download,
            spacy_config.auto_download,
        )
        spacy_model_path = (
            str(
                ensure_model_available(
                    provider="spacy",
                    model_name=spacy_config.model_name,
                    model_path=(
                        resolve_model_path(spacy_config.model_path)
                        if spacy_config.model_path is not None
                        else None
                    ),
                    auto_download=spacy_auto_download,
                )
            )
            if spacy_auto_download
            else spacy_config.model_path
        )
        return SpacyProvider(
            model_name=spacy_config.model_name,
            model_path=spacy_model_path,
            auto_download=spacy_auto_download,
            batch_size=spacy_config.batch_size,
        )

    if provider_name == "natasha":
        natasha_config = config.providers.natasha
        if not natasha_config.enabled:
            return None
        return NatashaProvider()

    qwen_config = config.providers.qwen
    if not qwen_config.enabled:
        return None
    return QwenProvider(
        model_name=qwen_config.model_name,
        model_path=ensure_model_available(
            provider="huggingface",
            model_name=qwen_config.model_name,
            model_path=(
                resolve_model_path(qwen_config.model_path)
                if qwen_config.model_path is not None
                else None
            ),
            auto_download=_effective_auto_download(
                config.auto_download,
                qwen_config.auto_download,
            ),
        ),
        auto_download=_effective_auto_download(
            config.auto_download,
            qwen_config.auto_download,
        ),
        device=qwen_config.device,
        threshold=qwen_config.threshold,
        max_context_chars=qwen_config.max_context_chars,
        max_new_tokens=qwen_config.max_new_tokens,
        labels=qwen_config.labels,
    )


def _effective_auto_download(
    global_auto_download: bool,
    provider_auto_download: bool | None,
) -> bool:
    if provider_auto_download is None:
        return global_auto_download
    return provider_auto_download
