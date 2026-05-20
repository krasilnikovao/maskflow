# MaskFlow

## RU — Локальный enterprise-ready сервис обезличивания и маскирования данных

MaskFlow — полностью локальный сервис для обнаружения, маскирования, псевдонимизации и обезличивания чувствительных данных.

Проект ориентирован на:

- DevSecOps;
- тестовые среды;
- передачу данных подрядчикам;
- безопасный анализ логов;
- аудит;
- CI/CD;
- обработку выгрузок 1С;
- обработку SQL-дампов;
- локальную обработку персональных данных.

MaskFlow не использует облачные сервисы, внешние API и не передает данные во внешние системы.

---

# Основные возможности

## Безопасность

- полностью офлайн архитектура;
- отсутствие внешних API;
- отсутствие телеметрии;
- локальная обработка данных;
- поддержка детерминированного маскирования;
- поддержка обратного демаскирования с шифрованием;
- безопасная обработка regex;
- таймауты выполнения;
- отсутствие логирования исходных значений.

## Поддерживаемые форматы

- TXT;
- JSON;
- XML;
- CSV;
- SQL dump;
- DOCX;
- XLSX;
- лог-файлы;
- текстовые выгрузки;
- данные 1С.

## Поддерживаемые типы данных

- email;
- телефоны;
- ИНН;
- GUID/UUID;
- ФИО;
- адреса;
- организации;
- банковские реквизиты;
- IP-адреса;
- домены;
- URL;
- паспортные данные;
- СНИЛС;
- пользовательские шаблоны.

## Режимы маскирования

- полное обезличивание;
- псевдонимизация;
- частичное маскирование;
- детерминированное HMAC-маскирование;
- сохранение формата значений.

## Архитектурные особенности

- потоковый процессинг;
- параллельная обработка;
- модульная архитектура;
- система плагинов;
- безопасные regex;
- поддержка юникода и кириллицы;
- поддержка UTF-8 и Windows-1251.

---

# Архитектура проекта

```text
maskflow/
├── configs/                # YAML-конфигурации
├── docker/                 # Docker-окружение
├── maskflow/
│   ├── audit/              # Audit trail и экспорт
│   ├── cli/                # CLI интерфейс
│   ├── core/               # Ядро pipeline
│   ├── detectors/          # Детекторы данных
│   ├── formats/            # Поддержка форматов файлов
│   ├── maskers/            # Алгоритмы маскирования
│   ├── plugins/            # Plugin system
│   ├── reports/            # Отчеты обработки
│   ├── rules/              # Правила маскирования
│   ├── security/           # Security utilities
│   ├── services/           # Сервисы обработки
│   ├── storage/            # Cache и reversible mapping
│   └── utils/              # Общие утилиты
├── plugins/                # Внешние плагины
├── scripts/                # Bootstrap/check scripts
├── tests/
│   ├── integration/
│   └── unit/
├── pyproject.toml
└── README.md
```

---

# Требования

## Linux

Рекомендуется:

- Ubuntu 24.04 LTS;
- Debian 12;
- Rocky Linux 9.

## Windows

Поддерживается:

- Windows 10/11;
- PowerShell 7+.

## Python

Требуется:

```text
Python >= 3.12
```

---

# Локальное развертывание

## 1. Клонирование репозитория

```bash
git clone git@github.com:krasilnikovao/maskflow.git
cd maskflow
```

---

# Автоматическое развертывание

Проект включает bootstrap-скрипты для автоматической подготовки окружения.

Bootstrap выполняет:

- создание virtualenv;
- обновление pip/setuptools/wheel;
- установку зависимостей;
- установку проекта в editable mode;
- установку dev-зависимостей;
- подготовку каталогов проекта;
- проверку окружения.

## Linux

```bash
./scripts/bootstrap.sh
```

Если требуется:

```bash
chmod +x ./scripts/bootstrap.sh
./scripts/bootstrap.sh
```

---

## Windows PowerShell

```powershell
./scripts/bootstrap.ps1
```

Если execution policy блокирует запуск:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
./scripts/bootstrap.ps1
```

---

# Ручное развертывание

Ручная установка рекомендуется только для:

- разработки bootstrap-скриптов;
- debugging;
- кастомных CI/CD pipelines;
- нестандартных окружений.

---

## 1. Создание virtualenv

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

---

## 2. Установка проекта

### Базовая установка

```bash
pip install -e .
```

### Установка с dev-зависимостями

```bash
pip install -e .[dev]
```

### Установка API режима

```bash
pip install -e .[api]
```

### Установка NLP модулей

```bash
pip install -e .[nlp]
```

### Полная установка

```bash
pip install -e .[dev,api,nlp]
```

---

# Быстрая проверка

```bash
maskflow --help
```

Пример:

```bash
maskflow mask input.txt output.txt
```

---

# Конфигурация

Основной конфигурационный файл:

```text
configs/default.yaml
```

---

# Детальное описание configs/default.yaml

## Pipeline

```yaml
pipeline:
  deterministic_secret: "set-via-MASKFLOW_SECRET"
```

### Назначение

Используется для:

- детерминированного HMAC-маскирования;
- генерации стабильных псевдонимов;
- одинаковой замены одинаковых значений.

### Важно

Никогда не храните production secret в Git.

Рекомендуется использовать:

```bash
export MASKFLOW_SECRET="strong-random-secret"
```

или:

```powershell
$env:MASKFLOW_SECRET="strong-random-secret"
```

---

# Правила маскирования

```yaml
rules:
  email:
    enabled: true
    mode: hmac
    prefix: EMAIL
```

## Параметры

### enabled

Включает или отключает правило.

```yaml
enabled: true
```

### mode

Определяет алгоритм маскирования.

Поддерживаемые режимы:

| Mode | Описание |
|---|---|
| hmac | Детерминированная HMAC-псевдонимизация |
| random | Случайная замена |
| static | Статическое значение |
| partial | Частичная маска |

### prefix

Префикс для выходного значения.

Пример:

```text
EMAIL_3fa92c11
PHONE_9ab811cc
```

---

# Поддерживаемые встроенные правила

```yaml
rules:
  email:
  phone:
  inn:
  guid:
```

---

# field_rules

```yaml
field_rules: {}
```

Используется для field-aware маскирования.

Пример:

```yaml
field_rules:
  password:
    detector: password
    mode: static
    value: "***MASKED***"
```

Полезно для:

- JSON;
- XML;
- SQL;
- API payloads;
- логов.

---

# runtime_limits

```yaml
runtime_limits:
  regex_timeout_seconds: 5
  file_timeout_seconds: 300
  max_workers: 4
```

## regex_timeout_seconds

Защита от catastrophic backtracking.

## file_timeout_seconds

Максимальное время обработки файла.

## max_workers

Количество parallel workers.

Рекомендуется:

| CPU | Workers |
|---|---|
| 4 core | 2-4 |
| 8 core | 4-8 |
| 16+ core | 8-16 |

---

# cache

```yaml
cache:
  enabled: true
  path: ".maskflow/entity-cache.json"
```

## Назначение

Используется для:

- стабильной псевдонимизации;
- ускорения обработки;
- повторного использования результатов.

## Важно

Не рекомендуется хранить cache в общих сетевых папках.

---

# reversible_mapping

```yaml
reversible_mapping:
  enabled: false
  path: ".maskflow/reversible-map.bin"
  encryption_key_env: "MASKFLOW_REVERSIBLE_KEY"
```

## Назначение

Позволяет восстанавливать исходные значения.

## Рекомендации

- включать только при необходимости;
- хранить ключ отдельно;
- использовать encrypted storage;
- ограничивать доступ к mapping.

## Переменная окружения

```bash
export MASKFLOW_REVERSIBLE_KEY="very-strong-key"
```

---

# Пример production-конфигурации

```yaml
pipeline:
  deterministic_secret: "set-via-MASKFLOW_SECRET"

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

runtime_limits:
  regex_timeout_seconds: 3
  file_timeout_seconds: 600
  max_workers: 8

cache:
  enabled: true
  path: "/var/lib/maskflow/cache.json"

reversible_mapping:
  enabled: false
```

---

# CLI

## Маскирование файла

```bash
maskflow mask input.json output.json
```

---

## Маскирование каталога

```bash
maskflow mask-dir ./input ./output
```

---

# Параметры CLI

## mask

| Параметр | Описание |
|---|---|
| --config | YAML-конфигурация |
| --log-level | INFO/DEBUG/WARNING |
| --json-logs | JSON logging |
| --dry-run | Анализ без записи |
| --overwrite | Перезапись файла |
| --plugins-dir | Каталог плагинов |
| --audit-report | Audit trail |

---

## mask-dir

| Параметр | Описание |
|---|---|
| --workers | Количество потоков |
| --report | JSON отчет |
| --audit-report | Audit trail |
| --overwrite | Перезапись файлов |

---

# Примеры

## TXT

### Вход

```text
Email: admin@example.com
Телефон: +7 999 123-45-67
ИНН: 7707083893
```

### Выход

```text
Email: EMAIL_92af8b1c
Телефон: PHONE_7bc331a1
ИНН: INN_3a29f77e
```

---

## JSON

### Вход

```json
{
  "email": "admin@example.com",
  "phone": "+79991234567"
}
```

### Выход

```json
{
  "email": "EMAIL_92af8b1c",
  "phone": "PHONE_7bc331a1"
}
```

---

# Dry-run режим

```bash
maskflow mask input.txt output.txt --dry-run
```

Режим:

- не изменяет файл;
- выполняет только анализ;
- показывает количество найденных совпадений.

---

# Audit Trail

```bash
maskflow mask \
  input.txt \
  output.txt \
  --audit-report audit.json
```

Используется для:

- аудита;
- compliance;
- DevSecOps;
- контроля обработки.

---

# Plugins

MaskFlow поддерживает внешние плагины.

Каталог:

```text
plugins/
```

Поддерживаются:

- detectors;
- maskers;
- format handlers;
- custom rules.

---

# Логирование

## Обычный режим

```bash
maskflow mask input.txt output.txt
```

## JSON logs

```bash
maskflow mask input.txt output.txt --json-logs
```

Полезно для:

- ELK;
- Loki;
- SIEM;
- audit pipelines.

---

# Docker

## Сборка

```bash
docker build -f docker/Dockerfile -t maskflow .
```

## Запуск

```bash
docker run --rm \
  -e MASKFLOW_SECRET=secret \
  -v $(pwd)/data:/data \
  maskflow \
  maskflow mask /data/input.txt /data/output.txt
```

---

# Проверка качества

## Ruff

```bash
ruff check .
```

## MyPy

```bash
mypy .
```

## Pytest

```bash
pytest
```

---

# Scripts

## Linux

```bash
./scripts/bootstrap.sh
./scripts/check.sh
```

## Windows

```powershell
./scripts/bootstrap.ps1
./scripts/check.ps1
```

---

# Безопасность

## Рекомендации

- не хранить secrets в Git;
- использовать ENV variables;
- ограничивать доступ к audit reports;
- хранить reversible mapping отдельно;
- использовать encrypted backups;
- ограничивать доступ к cache;
- выполнять регулярную ротацию ключей.

## Не рекомендуется

- использовать общий cache между окружениями;
- включать reversible mapping без необходимости;
- логировать оригинальные данные;
- использовать небезопасные regex.

---

# Roadmap

Планируемые возможности:

- REST API;
- streaming SQL parser;
- поддержка Parquet;
- поддержка Avro;
- поддержка Kafka;
- advanced NLP detectors;
- 1С-specific masking;
- policy engine;
- RBAC;
- Web UI.

---

# Лицензия

Internal / Proprietary.

---

# EN — Local enterprise-ready data masking service

MaskFlow is a fully local offline-first data masking and pseudonymization service designed for enterprise environments.

The project is intended for:

- DevSecOps;
- test environments;
- contractor data sharing;
- secure log analysis;
- CI/CD pipelines;
- database dumps;
- 1C exports;
- local PII processing.

MaskFlow never sends data to external APIs or cloud services.

---

# Key Features

## Security

- Fully offline architecture;
- no external APIs;
- no telemetry;
- local-only processing;
- deterministic masking;
- encrypted reversible mapping;
- regex safety controls;
- execution timeouts;
- no original value logging.

## Supported Formats

- TXT;
- JSON;
- XML;
- CSV;
- SQL dumps;
- DOCX;
- XLSX;
- logs;
- text exports;
- 1C data.

## Supported Data Types

- email addresses;
- phone numbers;
- Russian INN;
- GUID/UUID;
- personal names;
- organizations;
- bank details;
- IP addresses;
- domains;
- URLs;
- passport data;
- SNILS;
- custom patterns.

## Masking Modes

- Full anonymization;
- Pseudonymization;
- Partial masking;
- Deterministic HMAC masking;
- Format-preserving masking.

---

# Project Structure

```text
maskflow/
├── configs/
├── docker/
├── maskflow/
│   ├── audit/
│   ├── cli/
│   ├── core/
│   ├── detectors/
│   ├── formats/
│   ├── maskers/
│   ├── plugins/
│   ├── reports/
│   ├── rules/
│   ├── security/
│   ├── services/
│   ├── storage/
│   └── utils/
├── plugins/
├── scripts/
├── tests/
├── pyproject.toml
└── README.md
```

---

# Requirements

```text
Python >= 3.12
```

Supported operating systems:

- Linux;
- Windows 10/11.

---

# Local Deployment

## Clone Repository

```bash
git clone git@github.com:krasilnikovao/maskflow.git
cd maskflow
```

---

# Automatic Bootstrap

The project includes bootstrap scripts for automatic environment preparation.

Bootstrap scripts perform:

- virtualenv creation;
- pip/setuptools/wheel upgrade;
- dependency installation;
- editable project installation;
- development dependency installation;
- project directory initialization;
- environment validation.

## Linux

```bash
./scripts/bootstrap.sh
```

If required:

```bash
chmod +x ./scripts/bootstrap.sh
./scripts/bootstrap.sh
```

---

## Windows PowerShell

```powershell
./scripts/bootstrap.ps1
```

If PowerShell blocks execution:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
./scripts/bootstrap.ps1
```

---

# Manual Deployment

Manual installation is recommended only for:

- bootstrap development;
- debugging;
- custom CI/CD pipelines;
- non-standard environments.

---

## Create Virtual Environment

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

---

## Install Dependencies

### Base installation

```bash
pip install -e .
```

### Development dependencies

```bash
pip install -e .[dev]
```

### API dependencies

```bash
pip install -e .[api]
```

### NLP dependencies

```bash
pip install -e .[nlp]
```

### Full installation

```bash
pip install -e .[dev,api,nlp]
```

---

# Quick Start

```bash
maskflow --help
```

Example:

```bash
maskflow mask input.txt output.txt
```

---

# Configuration

Primary configuration file:

```text
configs/default.yaml
```

---

# Configuration Details

## pipeline

```yaml
pipeline:
  deterministic_secret: "set-via-MASKFLOW_SECRET"
```

Used for:

- deterministic HMAC masking;
- stable pseudonyms;
- repeatable replacements.

Recommended:

```bash
export MASKFLOW_SECRET="strong-random-secret"
```

---

# rules

```yaml
rules:
  email:
    enabled: true
    mode: hmac
    prefix: EMAIL
```

## Parameters

### enabled

Enables or disables the rule.

### mode

Supported values:

| Mode | Description |
|---|---|
| hmac | Deterministic HMAC pseudonymization |
| random | Random replacement |
| static | Static replacement |
| partial | Partial masking |

### prefix

Replacement prefix.

Example:

```text
EMAIL_92af8b1c
```

---

# runtime_limits

```yaml
runtime_limits:
  regex_timeout_seconds: 5
  file_timeout_seconds: 300
  max_workers: 4
```

Provides:

- regex safety;
- file execution limits;
- parallel processing controls.

---

# cache

```yaml
cache:
  enabled: true
  path: ".maskflow/entity-cache.json"
```

Used for:

- deterministic mapping;
- performance optimization;
- repeated value reuse.

---

# reversible_mapping

```yaml
reversible_mapping:
  enabled: false
  path: ".maskflow/reversible-map.bin"
  encryption_key_env: "MASKFLOW_REVERSIBLE_KEY"
```

Allows restoring original values.

Recommended only for restricted environments.

---

# CLI Commands

## Mask a file

```bash
maskflow mask input.json output.json
```

## Mask a directory

```bash
maskflow mask-dir ./input ./output
```

---

# CLI Options

## mask

| Option | Description |
|---|---|
| --config | YAML config |
| --log-level | Logging level |
| --json-logs | JSON logging |
| --dry-run | Analysis only |
| --overwrite | Overwrite output |
| --plugins-dir | External plugins |
| --audit-report | JSON audit report |

---

## mask-dir

| Option | Description |
|---|---|
| --workers | Parallel workers |
| --report | JSON batch report |
| --audit-report | Audit trail |
| --overwrite | Overwrite outputs |

---

# Examples

## TXT Example

### Input

```text
Email: admin@example.com
Phone: +1 555 123 4567
```

### Output

```text
Email: EMAIL_92af8b1c
Phone: PHONE_7bc331a1
```

---

# Dry Run

```bash
maskflow mask input.txt output.txt --dry-run
```

This mode:

- does not modify files;
- performs analysis only;
- prints match statistics.

---

# Audit Trail

```bash
maskflow mask \
  input.txt \
  output.txt \
  --audit-report audit.json
```

Useful for:

- compliance;
- audit pipelines;
- DevSecOps;
- reporting.

---

# Plugins

External plugins are supported.

Supported extension types:

- detectors;
- maskers;
- custom rules;
- format handlers.

---

# Logging

## Standard logs

```bash
maskflow mask input.txt output.txt
```

## JSON logs

```bash
maskflow mask input.txt output.txt --json-logs
```

Useful for:

- ELK;
- Loki;
- SIEM;
- centralized logging.

---

# Docker

## Build

```bash
docker build -f docker/Dockerfile -t maskflow .
```

## Run

```bash
docker run --rm \
  -e MASKFLOW_SECRET=secret \
  -v $(pwd)/data:/data \
  maskflow \
  maskflow mask /data/input.txt /data/output.txt
```

---

# Quality Checks

## Ruff

```bash
ruff check .
```

## MyPy

```bash
mypy .
```

## Pytest

```bash
pytest
```

---

# Scripts

## Linux

```bash
./scripts/bootstrap.sh
./scripts/check.sh
```

## Windows

```powershell
./scripts/bootstrap.ps1
./scripts/check.ps1
```

---

# Security Recommendations

- Never store secrets in Git;
- use environment variables;
- isolate audit reports;
- protect reversible mappings;
- encrypt backups;
- rotate secrets regularly.

Avoid:

- shared caches between environments;
- unnecessary reversible mapping;
- original value logging;
- unsafe regular expressions.

---

# Roadmap

Planned features:

- REST API;
- streaming SQL parser;
- Parquet support;
- Avro support;
- Kafka integration;
- advanced NLP detectors;
- 1C-aware masking;
- RBAC;
- Web UI.

---

# License

Internal / Proprietary.

