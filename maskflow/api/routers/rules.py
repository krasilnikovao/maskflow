from fastapi import APIRouter

from maskflow.api.schemas import RuleInfo
from maskflow.plugins.builtin import build_builtin_plugin_registry

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("", response_model=list[RuleInfo])
def list_rules() -> list[RuleInfo]:
    registry = build_builtin_plugin_registry()

    return [
        RuleInfo(
            name=name,
            detector=type(plugin.detector).__name__,
        )
        for name, plugin in sorted(registry.all().items())
    ]
