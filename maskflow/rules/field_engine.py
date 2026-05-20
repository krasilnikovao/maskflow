from maskflow.core.engine import MaskingEngine
from maskflow.rules.models import FieldRuleConfig


class FieldRuleEngine:
    def __init__(
        self,
        rules: dict[str, FieldRuleConfig],
        masking_engine: MaskingEngine,
    ) -> None:
        self.rules = {name.lower(): rule for name, rule in rules.items() if rule.enabled}
        self.masking_engine = masking_engine

    def process_field(
        self,
        field_name: str,
        value: str,
    ) -> str | None:
        rule = self.rules.get(field_name.lower())

        if rule is None:
            return self.masking_engine.process_text(value)

        if rule.action == "remove":
            return None

        if rule.action == "replace":
            return rule.replacement or ""

        if rule.action == "mask":
            return self.masking_engine.process_text(value)

        raise ValueError(f"Unsupported field rule action: {rule.action}")
