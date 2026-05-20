# MaskFlow Plugins

## RU — Система внешних плагинов MaskFlow

Каталог `plugins/` предназначен для подключения внешних enterprise-плагинов без изменения ядра MaskFlow.

Плагины позволяют:

- добавлять новые detectors;
- добавлять custom maskers;
- подключать обработчики форматов;
- реализовывать organization-specific правила;
- интегрировать внутренние корпоративные справочники;
- реализовывать кастомные политики обезличивания;
- расширять pipeline обработки.

MaskFlow использует plugin-first архитектуру и позволяет безопасно подключать внешние модули без модификации основного кода проекта.

---

# Основные принципы

## Безопасность

Внешние плагины:

- не должны отправлять данные во внешние сервисы;
- не должны использовать внешние API;
- не должны использовать телеметрию;
- не должны логировать оригинальные чувствительные данные;
- не должны сохранять исходные значения без необходимости;
- не должны изменять глобальное runtime state;
- не должны выполнять network requests по умолчанию;
- не должны ломать структуру входных данных.

## Производительность

Плагины должны:

- поддерживать streaming processing;
- минимизировать потребление памяти;
- избегать full-file loading;
- поддерживать batch processing;
- учитывать large-file scenarios.

## Совместимость

Плагины должны:

- поддерживать Python 3.12+;
- учитывать Unicode;
- корректно работать с кириллицей;
- поддерживать UTF-8 и Windows-1251;
- учитывать особенности российских данных.

---

# Структура каталога plugins/

```text
plugins/
├── README.md
├── company_rules/
│   ├── __init__.py
│   ├── detector.py
│   ├── masker.py
│   └── plugin.py
├── custom_1c/
│   ├── __init__.py
│   ├── detector.py
│   ├── rules.py
│   └── plugin.py
└── shared/
    ├── dictionaries/
    └── utils/
```

---

# Поддерживаемые типы расширений

## Detectors

Используются для обнаружения:

- custom identifiers;
- внутренних ID;
- корпоративных кодов;
- 1С объектов;
- внутренних справочников;
- proprietary форматов.

Примеры:

- номера договоров;
- внутренние GUID;
- custom артикулы;
- SAP IDs;
- 1С ссылки.

---

## Maskers

Используются для:

- custom pseudonymization;
- format-preserving masking;
- reversible mapping;
- dictionary replacement;
- enterprise-specific transformations.

---

## Format Handlers

Используются для:

- proprietary exports;
- нестандартных логов;
- custom XML;
- 1С выгрузок;
- внутренних текстовых форматов.

---

## Rules

Используются для:

- field-aware masking;
- conditional masking;
- context-aware masking;
- organization policies;
- compliance rules.

---

# Plugin API

Каждый плагин должен экспортировать:

```python
from maskflow.plugins.registry import PluginRegistry
from maskflow.plugins.spec import PluginSpec


def register_plugins(registry: PluginRegistry) -> None:
    registry.register(
        PluginSpec(
            name="custom_rule",
            detector=CustomDetector(),
            masker_factory=CustomMasker,
        )
    )
```

---

# PluginSpec

## Основные параметры

```python
PluginSpec(
    name="custom_rule",
    detector=CustomDetector(),
    masker_factory=CustomMasker,
)
```

---

## name

Уникальное имя плагина.

Рекомендуется:

```text
company_inn
sap_customer_id
custom_1c_reference
```

---

## detector

Экземпляр detector-класса.

Detector отвечает за:

- поиск совпадений;
- извлечение сущностей;
- безопасный regex matching;
- field-aware detection.

---

## masker_factory

Factory для создания masker.

Masker отвечает за:

- замену значений;
- pseudonymization;
- deterministic mapping;
- format preservation.

---

# Пример detector

```python
from dataclasses import dataclass
import regex as re


@dataclass(slots=True)
class ContractDetector:
    pattern: re.Pattern = re.compile(
        r"\bDOG-\d{6}\b",
        flags=re.IGNORECASE,
        timeout=2,
    )

    def detect(self, text: str):
        return self.pattern.finditer(text)
```

---

# Пример masker

```python
import hashlib


class ContractMasker:
    def __init__(self, secret: str):
        self.secret = secret

    def mask(self, value: str) -> str:
        digest = hashlib.sha256(
            f"{self.secret}:{value}".encode()
        ).hexdigest()[:10]

        return f"CONTRACT_{digest}"
```

---

# Полный пример плагина

## plugin.py

```python
from maskflow.plugins.registry import PluginRegistry
from maskflow.plugins.spec import PluginSpec

from .detector import ContractDetector
from .masker import ContractMasker


def register_plugins(registry: PluginRegistry) -> None:
    registry.register(
        PluginSpec(
            name="contract_detector",
            detector=ContractDetector(),
            masker_factory=ContractMasker,
        )
    )
```

---

# Загрузка плагинов

## CLI

```bash
maskflow mask \
  input.txt \
  output.txt \
  --plugins-dir ./plugins
```

---

# Автозагрузка

Рекомендуемая структура:

```text
plugins/
├── plugin_a/
├── plugin_b/
└── plugin_c/
```

Каждый каталог должен содержать:

```text
plugin.py
```

---

# Конфигурация плагинов

## YAML

```yaml
plugins:
  enabled: true
  directory: ./plugins
```

---

# Plugin-specific settings

```yaml
plugin_settings:
  contract_detector:
    enabled: true
    preserve_format: true
    deterministic: true
```

---

# Работа с 1С

Плагины могут использоваться для:

- маскирования ссылок 1С;
- обработки GUID объектов;
- анализа BSL-кода;
- обработки технологического журнала;
- маскирования SQL-структур регистров;
- обработки XML/DT выгрузок.

## Примеры 1С сущностей

```text
Справочник.Номенклатура
Документ.РеализацияТоваровУслуг
РегистрСведений.АналитикаУчета
```

---

# Рекомендации по regex

## Безопасные regex

Используйте:

```python
import regex as re

re.compile(pattern, timeout=2)
```

## Не рекомендуется

- catastrophic backtracking;
- nested quantifiers;
- unbounded wildcards;
- overly generic patterns.

---

# Logging

## Разрешено

```python
logger.info("Detector executed", detector="contract")
```

## Запрещено

```python
logger.info("Matched value", value=original_value)
```

---

# Thread Safety

Плагины должны:

- быть thread-safe;
- избегать global mutable state;
- поддерживать multiprocessing;
- избегать shared mutable caches.

---

# Error Handling

Рекомендуется:

```python
try:
    process()
except Exception:
    logger.exception("Plugin execution failed")
```

Не рекомендуется:

- suppress exceptions;
- скрывать critical failures;
- логировать sensitive payloads.

---

# Unit Tests

Рекомендуемая структура:

```text
tests/
└── plugins/
    ├── test_contract_detector.py
    └── test_contract_masker.py
```

---

# Пример теста

```python
from plugins.company_rules.detector import ContractDetector


def test_contract_detection():
    detector = ContractDetector()

    matches = list(
        detector.detect("DOG-123456")
    )

    assert len(matches) == 1
```

---

# Docker

## Подключение каталога плагинов

```bash
docker run --rm \
  -v $(pwd)/plugins:/plugins \
  maskflow \
  maskflow mask \
    /data/input.txt \
    /data/output.txt \
    --plugins-dir /plugins
```

---

# Security Recommendations

## Рекомендуется

- review all third-party plugins;
- isolate plugin execution;
- validate regex patterns;
- use deterministic masking;
- audit plugin logging;
- restrict filesystem access.

## Запрещено

- external network access;
- cloud integrations;
- unsafe regex;
- plaintext reversible mapping;
- storing original values.

---

# Best Practices

## Рекомендуется

- use type hints;
- use dataclasses or pydantic;
- use slots=True;
- keep plugins modular;
- minimize dependencies;
- write unit tests.

## Запрещено

- heavy NLP models inside plugins;
- mutable globals;
- side effects;
- large in-memory caches.

---

# Roadmap

Планируемые возвожности плагинов:

- NLP detector plugins;
- ML-assisted masking;
- streaming format plugins;
- policy plugins;
- RBAC-aware plugins;
- Kafka connectors;
- enterprise dictionary plugins.

---

# EN — MaskFlow Plugin System

The `plugins/` directory is предназначен for enterprise-specific extensions without modifying the MaskFlow core.

Plugins allow:

- custom detectors;
- custom maskers;
- proprietary format handlers;
- organization-specific rules;
- enterprise pseudonymization logic;
- custom processing pipelines.

MaskFlow follows a plugin-first architecture allowing secure extension of the platform.

---

# Core Principles

## Security

External plugins must NOT:

- send data to external services;
- use cloud APIs;
- use telemetry;
- log original sensitive values;
- store original values unnecessarily;
- mutate global runtime state;
- perform network requests by default.

---

# Supported Extension Types

## Detectors

Used for detecting:

- proprietary identifiers;
- enterprise codes;
- custom GUIDs;
- SAP identifiers;
- 1C references.

---

## Maskers

Used for:

- pseudonymization;
- deterministic masking;
- format-preserving replacement;
- reversible mapping;
- enterprise-specific transformations.

---

## Format Handlers

Used for:

- proprietary exports;
- internal logs;
- custom XML;
- 1C exports;
- organization-specific formats.

---

# Plugin API

Each plugin must export:

```python
from maskflow.plugins.registry import PluginRegistry
from maskflow.plugins.spec import PluginSpec


def register_plugins(registry: PluginRegistry) -> None:
    registry.register(
        PluginSpec(
            name="custom_rule",
            detector=CustomDetector(),
            masker_factory=CustomMasker,
        )
    )
```

---

# Detector Example

```python
from dataclasses import dataclass
import regex as re


@dataclass(slots=True)
class ContractDetector:
    pattern: re.Pattern = re.compile(
        r"\bDOG-\d{6}\b",
        flags=re.IGNORECASE,
        timeout=2,
    )

    def detect(self, text: str):
        return self.pattern.finditer(text)
```

---

# Masker Example

```python
import hashlib


class ContractMasker:
    def __init__(self, secret: str):
        self.secret = secret

    def mask(self, value: str) -> str:
        digest = hashlib.sha256(
            f"{self.secret}:{value}".encode()
        ).hexdigest()[:10]

        return f"CONTRACT_{digest}"
```

---

# Plugin Loading

## CLI

```bash
maskflow mask \
  input.txt \
  output.txt \
  --plugins-dir ./plugins
```

---

# Plugin Configuration

```yaml
plugins:
  enabled: true
  directory: ./plugins
```

---

# Thread Safety

Plugins should:

- be thread-safe;
- avoid mutable globals;
- support multiprocessing;
- avoid shared mutable caches.

---

# Logging Rules

## Allowed

```python
logger.info("Plugin executed")
```

## Forbidden

```python
logger.info("Matched value", value=original_value)
```

---

# Unit Tests

Recommended structure:

```text
tests/plugins/
```

Example:

```python
from plugins.company_rules.detector import ContractDetector


def test_contract_detection():
    detector = ContractDetector()

    matches = list(
        detector.detect("DOG-123456")
    )

    assert len(matches) == 1
```

---

# Docker

```bash
docker run --rm \
  -v $(pwd)/plugins:/plugins \
  maskflow \
  maskflow mask \
    /data/input.txt \
    /data/output.txt \
    --plugins-dir /plugins
```

---

# Security Recommendations

Recommended:

- review all plugins;
- isolate plugin execution;
- validate regex safety;
- audit logging;
- restrict filesystem access.

Avoid:

- external network access;
- cloud integrations;
- unsafe regex;
- plaintext mappings;
- original value storage.

---

# Best Practices

Recommended:

- use type hints;
- use dataclasses or pydantic;
- keep plugins modular;
- minimize dependencies;
- write unit tests.

Avoid:

- large NLP models inside plugins;
- mutable globals;
- hidden side effects;
- large in-memory caches.

---

# Roadmap

Planned features:

- NLP plugins;
- ML-assisted detectors;
- streaming parsers;
- Kafka plugins;
- enterprise dictionary plugins;
- policy-aware masking plugins.

---

# License

Internal / Proprietary.
