# MaskFlow

## Русский

MaskFlow — локальная enterprise-grade платформа для маскировки, обезличивания и псевдонимизации данных.

Проект предназначен для безопасной офлайн-обработки чувствительных корпоративных данных:

- тестовых и dev-стендов;
- передачи данных подрядчикам;
- DevSecOps-пайплайнов;
- анализа логов;
- диагностики инцидентов;
- интеграционного тестирования;
- экосистем 1С.

### Основные возможности

- Полностью локальная работа без облаков и внешних API
- Детерминированная маскировка
- Поддержка reversible pseudonymization
- Шифрованное хранение mapping
- Structured audit trail
- JSON/XML/CSV/SQL/TXT/DOCX/XLSX support
- Поддержка внешних plugins
- Потоковая обработка больших файлов
- Защита от ReDoS
- Timeout protection
- Atomic writes
- Windows/Linux support
- Поддержка Windows-1251 / CP866 / UTF-8
- Foundation для 1С environments

### Быстрый старт

```bash
uv venv
uv sync --extra dev
```

Маскирование файла:

```bash
maskflow mask input.json output.json
```

Маскирование каталога:

```bash
maskflow mask-dir ./input ./output
```

Генерация audit report:

```bash
maskflow mask-dir ./input ./output \
  --audit-report audit.json
```

---

## English

# MaskFlow

Local enterprise-grade data masking, anonymization, and pseudonymization platform.

MaskFlow is designed for secure offline anonymization of sensitive corporate data:

- development environments;
- contractor data transfer;
- test databases;
- DevSecOps pipelines;
- log analysis;
- incident diagnostics;
- enterprise integrations;
- 1C ecosystems.

The project works fully locally without external APIs or cloud services.

---

# Features

## Security-first architecture

- Fully offline
- No external API calls
- No telemetry
- No cloud dependencies
- No plaintext cache storage
- Encrypted reversible mappings
- Structured forensic-safe audit logs
- ReDoS-aware regex processing
- Timeout protection for detectors

---

## Supported formats

### Structured formats

- JSON
- XML
- CSV
- SQL dumps
- XLSX
- DOCX

### Text formats

- TXT
- Logs
- Arbitrary text
- 1C exports

---

## Supported data types

- Email
- Phone numbers
- INN / ИНН
- GUID / UUID
- User comments
- URLs
- IP addresses
- Logins
- Arbitrary text patterns

Architecture supports custom enterprise detectors and plugins.

---

# Key capabilities

## Deterministic masking

Same input → same masked value:

```text
admin@example.com -> EMAIL_7d83d9e3c2d1a1f4
```

Works across:

- files;
- runs;
- systems;
- pipelines.

---

## Persistent deterministic cache

Optional persistent cache provides stable pseudonyms between runs:

```yaml
cache:
  enabled: true
  path: ".maskflow/entity-cache.json"
```

---

## Reversible pseudonymization

Optional encrypted reversible registry:

```yaml
reversible_mapping:
  enabled: true
  path: ".maskflow/reversible-map.bin"
  encryption_key_env: "MASKFLOW_REVERSIBLE_KEY"
```

Features:

- encrypted local storage;
- Fernet encryption;
- ENV-only encryption keys;
- no plaintext mapping on disk.

---

## Structured audit trail

Optional forensic-safe audit export:

```bash
maskflow mask input.json output.json \
  --audit-report audit.json
```

Audit artifacts contain:

- processing events;
- detector statistics;
- timing information;
- masking analytics;
- compliance-safe metadata.

No original sensitive values are stored.

---

# Installation

## Requirements

- Python 3.12+
- Windows / Linux

---

## Install with uv (recommended)

```bash
uv venv
uv sync --extra dev
```

---

## Install with pip

```bash
python -m venv .venv

# Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -e .[dev]
```

---

# Quick start

## Mask a single file

```bash
maskflow mask input.json output.json
```

## Mask directory recursively

```bash
maskflow mask-dir ./input ./output
```

## Generate audit report

```bash
maskflow mask-dir ./input ./output \
  --audit-report audit.json
```

## Use external plugins

```bash
maskflow mask input.txt output.txt \
  --plugins-dir ./plugins
```

---

# Configuration

```yaml
pipeline:
  deterministic_secret: "CHANGE_ME"

rules:
  email:
    enabled: true
    mode: hmac
    prefix: EMAIL

  phone:
    enabled: true
    mode: hmac
    prefix: PHONE

  inn:
    enabled: true
    mode: hmac
    prefix: INN

  guid:
    enabled: true
    mode: hmac
    prefix: GUID

field_rules: {}

runtime_limits:
  regex_timeout_seconds: 5
  file_timeout_seconds: 300
  max_workers: 4

cache:
  enabled: true
  path: ".maskflow/entity-cache.json"

reversible_mapping:
  enabled: false
  path: ".maskflow/reversible-map.bin"
  encryption_key_env: "MASKFLOW_REVERSIBLE_KEY"
```

---

# Development

Run checks:

```bash
scripts/check.ps1
```

Includes:

- Ruff
- MyPy
- Pytest
