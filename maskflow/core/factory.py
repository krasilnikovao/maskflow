from pathlib import Path

from maskflow.core.bundle import EngineBundle
from maskflow.core.engine import MaskingEngine
from maskflow.core.registry import Registry
from maskflow.detectors.nlp import NlpEntityDetector
from maskflow.detectors.regex_base import RegexDetector
from maskflow.maskers.hmac_masker import HmacMasker
from maskflow.nlp.factory import build_nlp_pipeline
from maskflow.nlp.labels import DEFAULT_ENTITY_TYPES
from maskflow.plugins.builtin import build_builtin_plugin_registry
from maskflow.plugins.loader import load_external_plugins
from maskflow.plugins.registry import PluginRegistry
from maskflow.rules.models import AppConfig, MaskingMode, RuleConfig
from maskflow.runtime.paths import resolve_data_path
from maskflow.storage.encrypted_mapping import EncryptedMappingStore
from maskflow.storage.entity_cache import EntityCache

# Modes that have a complete masker implementation. Other MaskingMode values are
# recognised by the type system but raise NotImplementedError until implemented.
_IMPLEMENTED_MODES: frozenset[MaskingMode] = frozenset({"hmac"})
_NLP_ENTITY_RULES: frozenset[str] = frozenset(DEFAULT_ENTITY_TYPES)
_DEFAULT_NLP_PREFIXES: dict[str, str] = {
    "person": "PERSON",
    "organization": "ORG",
    "location": "LOC",
    "address": "ADDRESS",
}


def build_engine_bundle_from_config(
    config: AppConfig,
    plugin_registry: PluginRegistry | None = None,
    plugins_dir: Path | None = None,
) -> EngineBundle:
    runtime_registry = Registry()
    plugins = plugin_registry or build_builtin_plugin_registry()
    if plugins_dir is not None:
        load_external_plugins(
            registry=plugins,
            plugins_dir=plugins_dir,
        )

    entity_cache = None
    reversible_mapping = None

    if config.reversible_mapping.enabled:
        reversible_mapping = EncryptedMappingStore(
            path=resolve_data_path(config.reversible_mapping.path),
            encryption_key_env=config.reversible_mapping.encryption_key_env,
        )

    if config.cache.enabled:
        entity_cache = EntityCache(
            resolve_data_path(config.cache.path),
        )

    nlp_pipeline = build_nlp_pipeline(config.nlp)
    if nlp_pipeline is not None:
        runtime_registry.register_detector(NlpEntityDetector(nlp_pipeline))

    for rule_name, rule in config.rules.items():
        if not rule.enabled:
            continue

        if rule_name in _NLP_ENTITY_RULES:
            if nlp_pipeline is None:
                raise ValueError(
                    f"Rule '{rule_name}' requires nlp.enabled=true"
                )
            _register_nlp_masker(
                runtime_registry=runtime_registry,
                rule_name=rule_name,
                rule=rule,
                secret=config.pipeline.deterministic_secret,
                entity_cache=entity_cache,
                reversible_mapping=reversible_mapping,
            )
            continue

        try:
            plugin = plugins.get(rule_name)
            detector = plugin.detector

            if isinstance(detector, RegexDetector):
                detector = detector.with_timeout(
                    config.runtime_limits.regex_timeout_seconds,
                )
        except ValueError as error:
            raise ValueError(f"Unknown rule: {rule_name}") from error

        runtime_registry.register_detector(detector)

        if rule.mode not in _IMPLEMENTED_MODES:
            raise NotImplementedError(
                f"Masking mode '{rule.mode}' is defined but not yet implemented. "
                f"Currently supported modes: {sorted(_IMPLEMENTED_MODES)}"
            )

        # Derive prefix from config; fall back to the upper-cased rule name so
        # callers do not need to repeat the rule name in every config file.
        effective_prefix = rule.prefix or rule_name.upper()

        runtime_registry.register_masker(
            detector_name=rule_name,
            masker=plugin.masker_factory(
                config.pipeline.deterministic_secret,
                effective_prefix,
                entity_cache,
                reversible_mapping,
            ),
        )

    if nlp_pipeline is not None:
        for rule_name in DEFAULT_ENTITY_TYPES:
            if rule_name in config.rules:
                continue

            _register_nlp_masker(
                runtime_registry=runtime_registry,
                rule_name=rule_name,
                rule=RuleConfig(prefix=_DEFAULT_NLP_PREFIXES[rule_name]),
                secret=config.pipeline.deterministic_secret,
                entity_cache=entity_cache,
                reversible_mapping=reversible_mapping,
            )

    engine = MaskingEngine(
        detectors=runtime_registry.detectors,
        maskers=runtime_registry.maskers,
    )

    return EngineBundle(
        engine=engine,
        entity_cache=entity_cache,
        reversible_mapping=reversible_mapping,
    )


def _register_nlp_masker(
    runtime_registry: Registry,
    rule_name: str,
    rule: RuleConfig,
    secret: str,
    entity_cache: EntityCache | None,
    reversible_mapping: EncryptedMappingStore | None,
) -> None:
    if rule.mode not in _IMPLEMENTED_MODES:
        raise NotImplementedError(
            f"Masking mode '{rule.mode}' is defined but not yet implemented. "
            f"Currently supported modes: {sorted(_IMPLEMENTED_MODES)}"
        )

    effective_prefix = rule.prefix or rule_name.upper()
    runtime_registry.register_masker(
        detector_name=rule_name,
        masker=HmacMasker(
            secret,
            effective_prefix,
            entity_cache,
            reversible_mapping,
        ),
    )
