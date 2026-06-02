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

| Режим | Описание | Пример |
|---|---|---|
| `hmac` | Детерминированная HMAC-псевдонимизация | `EMAIL_92af8b1c` |
| `partial` | Частичная маска, сохраняет начало/домен | `ex***@mail.ru` |
| `preserve_format` | Формат-сохраняющая замена (цифра→цифра, буква→буква) | `7707083893 → 3841259607` |
| `redact` | Полное замещение фиксированным токеном | `EMAIL_REDACTED` |

## Архитектурные особенности

- потоковый процессинг;
- параллельная обработка;
- модульная архитектура;
- система плагинов с верификацией SHA-256;
- безопасные regex с таймаутами;
- поддержка юникода и кириллицы;
- поддержка UTF-8 и Windows-1251;
- умная обработка LOG-файлов (сохранение timestamps, levels, stack traces).

---

# Архитектура проекта

```text
maskflow/
├── configs/                # YAML-конфигурации
├── data/                   # runtime volume, не хранится в git
├── docker/                 # Docker-окружение
├── maskflow/
│   ├── api/                # REST API adapter
│   ├── audit/              # Audit trail и экспорт
│   ├── cli/                # CLI интерфейс
│   ├── core/               # Ядро pipeline
│   ├── detectors/          # Детекторы данных
│   ├── formats/            # Поддержка форматов файлов
│   ├── maskers/            # Алгоритмы маскирования
│   ├── plugins/            # Plugin system
│   ├── reports/            # Отчеты обработки
│   ├── rules/              # Правила маскирования
│   ├── runtime/            # ENV, settings и runtime paths
│   ├── security/           # Security utilities
│   ├── services/           # Сервисы обработки
│   ├── storage/            # Cache и reversible mapping
│   ├── utils/              # Общие утилиты
│   └── web_htmx/           # Server-rendered HTMX UI adapter
├── plugins/                # Внешние плагины
├── scripts/                # Bootstrap/check scripts
├── tests/
│   ├── integration/
│   └── unit/
├── pyproject.toml
└── README.md
```

`api/`, `web_htmx/` и `cli/` являются входными адаптерами. Общая логика остается в
`services/`, `core/`, `rules/`, `formats`, `storage`, `reports` и `audit`.
Все runtime-пути строятся от `MASKFLOW_DATA_DIR`, по умолчанию `data`.

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
- установку зависимостей;
- выбор профиля установки через интерактивное меню;
- подготовку каталогов проекта;
- создание `.env` из `.env.example`, если файл отсутствует;
- проверку окружения.

Профили установки:

| Профиль | Extras | Назначение |
|---|---|---|
| base | - | минимальная runtime-установка |
| dev | dev | разработка, Ruff, MyPy, Pytest |
| download | download | скачивание моделей из Hugging Face |
| nlp | download,nlp | GLiNER, spaCy, Natasha |
| all | dev,download,nlp | полный профиль разработки NLP |

## Linux

```bash
./scripts/bootstrap.sh
```

Без интерактивного меню:

```bash
./scripts/bootstrap.sh --profile nlp --skip-validation
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

Без интерактивного меню:

```powershell
.\scripts\bootstrap.ps1 -Profile nlp -SkipValidation
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

### Установка поддержки скачивания моделей

```bash
pip install -e .[download]
```

### Установка NLP модулей

```bash
pip install -e .[download,nlp]
```

### Полная установка

```bash
pip install -e .[dev,api,download,nlp]
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

## NLP и локальные модели

NLP выключен по умолчанию. Базовая установка MaskFlow остается offline-first и
не требует ML-зависимостей.

Модели хранятся в runtime-каталоге:

```text
data/models/
```

В Docker этот каталог находится внутри volume `/data/models`.

Основные ENV-переменные:

```text
MASKFLOW_DEFAULT_CONFIG=configs/default.yaml
MASKFLOW_EXTRAS=download,nlp
HF_TOKEN=
MASKFLOW_NLP_ENABLED=false
MASKFLOW_NLP_AUTO_DOWNLOAD=false
MASKFLOW_GLINER_ENABLED=false
MASKFLOW_GLINER_MODEL=urchade/gliner_multi-v2.1
MASKFLOW_GLINER_MODEL_PATH=
MASKFLOW_GLINER_DEVICE=cpu
MASKFLOW_SPACY_ENABLED=false
MASKFLOW_SPACY_MODEL=ru_core_news_lg
MASKFLOW_SPACY_MODEL_PATH=
MASKFLOW_NATASHA_ENABLED=false
MASKFLOW_QWEN_ENABLED=false
MASKFLOW_QWEN_MODEL=Qwen/Qwen2.5-Coder-7B-Instruct
MASKFLOW_QWEN_MODEL_PATH=
MASKFLOW_QWEN_DEVICE=cpu
```

ENV-переменные перекрывают YAML только когда они реально заданы в окружении.
Пустые строковые значения вроде `MASKFLOW_GLINER_MODEL_PATH=` игнорируются, чтобы
Docker Compose мог оставлять путь модели в YAML.

`MASKFLOW_DEFAULT_CONFIG` задает YAML-конфиг для CLI/Web/API. В Docker можно
использовать конфиг, встроенный в образ, например `configs/examples/nlp.yaml`,
или файл из подключенного volume, например `/data/configs/my-config.yaml`.

`HF_TOKEN` используется `huggingface_hub` для private/gated моделей и лимитов
Hugging Face API. Публичные модели обычно скачиваются без токена. Не передавайте
`HF_TOKEN` как Docker build arg, чтобы не записать секрет в image layers.

`auto_download` выключен по умолчанию. Для production рекомендуется заранее
разместить модели в `data/models` и явно указать `model_path` в YAML.

Минимальная NLP-секция:

```yaml
nlp:
  enabled: true
  auto_download: false
  providers:
    gliner:
      enabled: true
      model_name: "urchade/gliner_multi-v2.1"
      model_path: "huggingface/urchade__gliner_multi-v2.1"
    spacy:
      enabled: true
      model_name: "ru_core_news_lg"
    natasha:
      enabled: true
    qwen:
      enabled: false
```

Подготовить модель вручную:

```bash
maskflow prepare-models --config configs/default.yaml --provider gliner --auto-download
maskflow prepare-models --config configs/default.yaml --provider spacy --auto-download
```

Команда читает только NLP-настройки и не требует production `MASKFLOW_SECRET`.
Без `--auto-download` она проверяет, что модель уже есть локально.
Для spaCy модель сохраняется в `data/models/spacy/<model_name>`, а не
устанавливается в системный Python контейнера.

Для Web-маскирования через Docker нужны три условия:

- образ собран с `MASKFLOW_EXTRAS=download,nlp`;
- в runtime окружении включены `MASKFLOW_NLP_ENABLED=true` и хотя бы один provider;
- выбранный `MASKFLOW_DEFAULT_CONFIG` доступен внутри контейнера.

При `MASKFLOW_LOG_LEVEL=DEBUG` в логах обработки файла должен появиться detector
`nlp` в `detector_timings_ms`. Если его нет, NLP pipeline не был включен в
конфиге, который реально загрузил Web.

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

| Mode | Описание | Пример результата |
|---|---|---|
| `hmac` | Детерминированная HMAC-псевдонимизация. Одно значение всегда → один токен. Требует `deterministic_secret`. | `EMAIL_92af8b1c` |
| `partial` | Частичная маска: email сохраняет домен, остальное — крайние символы. | `ex***@mail.ru` |
| `preserve_format` | Цифра→цифра, буква→буква, разделители без изменений. Длина сохраняется. | `+7 (412) 853-91-24` |
| `redact` | Полное замещение. Быстро и необратимо. | `EMAIL_REDACTED` |

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
  email:      # адреса электронной почты
  phone:      # российские телефоны (+7, 8)
  inn:        # ИНН 10/12 цифр с контрольной суммой
  kpp:        # КПП
  ogrn:       # ОГРН/ОГРНИП
  snils:      # СНИЛС
  bank_account: # расчётные счета (20 цифр)
  bik:        # БИК банка
  guid:       # UUID/GUID
  ip_address: # IPv4-адреса
  url:        # URL
```

---

# Обработка LOG-файлов

LOG-процессор (`.log`) обрабатывает файлы построчно и защищает структурные элементы:

- **Stack traces** (`at com.example...`, `File "path.py"`, `Caused by:`) — строка сохраняется целиком, PII там не бывает;
- **Префикс строки** (timestamp + level + имя логгера) — не маскируется;
- **Message-часть** — маскируется детекторами.

Поддерживаемые форматы:

| Формат | Пример |
|---|---|
| ISO / Python / Java | `2024-01-15 10:23:45,123 INFO root - message` |
| ISO T / structlog | `2024-01-15T10:23:45.123Z [ERROR] message` |
| Apache / nginx | `[15/Jan/2024:10:23:45 +0000] "GET /path" 200` |
| 1С техжурнал | `{10:23:45.123-0,PROC,5}event=Connect,...` |

Пример маскировки:

```text
# Вход
2024-01-15 10:23:45,123 ERROR app - failed for user@example.com
    at com.example.Service.call(Service.java:42)

# Выход
2024-01-15 10:23:45,123 ERROR app - failed for EMAIL_92af8b1c
    at com.example.Service.call(Service.java:42)
```

`.txt`-файлы по-прежнему обрабатываются через потоковый `TextProcessor` без учёта структуры.

---

# Безопасность плагинов

При загрузке внешних плагинов без верификации SHA-256 в лог выводится предупреждение:

```text
[warning] external_plugins_no_hash_verification
  note='trusted_hashes not provided — plugin integrity is NOT verified.'
```

Для production рекомендуется передавать список разрешённых хэшей:

```bash
maskflow mask input.txt output.txt --plugins-dir ./plugins
# В Python API:
load_external_plugins(registry, plugins_dir, trusted_hashes={"sha256hex..."})
```

Вычислить хэш плагина:

```bash
sha256sum plugins/my_plugin.py
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

### Выход (mode: hmac)

```json
{
  "email": "EMAIL_92af8b1c",
  "phone": "PHONE_7bc331a1"
}
```

---

## Режим partial

### Вход

```text
Email: admin@example.com
Телефон: +79991234567
```

### Выход

```text
Email: ad***@example.com
Телефон: +7***4567
```

---

## Режим preserve_format

### Вход

```text
ИНН: 7707083893
Телефон: +7 (999) 123-45-67
```

### Выход (длина и формат сохранены)

```text
ИНН: 3841259607
Телефон: +7 (412) 853-91-24
```

---

## Режим redact

### Вход

```text
Email: admin@example.com
```

### Выход

```text
Email: EMAIL_REDACTED
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

С NLP-зависимостями:

```bash
docker build \
  --build-arg MASKFLOW_EXTRAS=download,nlp \
  -f docker/Dockerfile \
  -t maskflow:nlp .
```

Для `docker compose` задайте в `.env`, затем пересоберите контейнер:

```text
MASKFLOW_DEFAULT_CONFIG=configs/examples/nlp.yaml
MASKFLOW_EXTRAS=download,nlp
HF_TOKEN=hf_...
MASKFLOW_NLP_ENABLED=true
MASKFLOW_NLP_AUTO_DOWNLOAD=true
MASKFLOW_GLINER_ENABLED=true
```

Для своего runtime-конфига положите файл в `data/configs`, затем укажите путь
внутри контейнера:

```text
MASKFLOW_DEFAULT_CONFIG=/data/configs/my-config.yaml
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
./scripts/bootstrap.sh --profile dev
./scripts/check.sh
```

## Windows

```powershell
.\scripts\bootstrap.ps1 -Profile dev
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

## Реализовано

- ✅ Режим `partial` — частичная маска;
- ✅ Режим `preserve_format` — формат-сохраняющая замена;
- ✅ Режим `redact` — полное замещение;
- ✅ LOG-процессор с защитой структурных элементов;
- ✅ Верификация плагинов по SHA-256;
- ✅ Оптимизация демаскирования (O(N) вместо O(N×M));
- ✅ Hard limit для JSON >100 MB.

## Планируется

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

| Mode | Description | Example |
|---|---|---|
| `hmac` | Deterministic HMAC pseudonymization | `EMAIL_92af8b1c` |
| `partial` | Partial mask, preserves domain/suffix | `ex***@mail.ru` |
| `preserve_format` | Format-preserving replacement (digit→digit, letter→letter) | `7707083893 → 3841259607` |
| `redact` | Full replacement with a fixed token | `EMAIL_REDACTED` |

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
- dependency installation;
- interactive installation profile selection;
- project directory initialization;
- `.env` creation from `.env.example` when missing;
- environment validation.

Installation profiles:

| Profile | Extras | Purpose |
|---|---|---|
| base | - | minimal runtime install |
| dev | dev | development, Ruff, MyPy, Pytest |
| download | download | Hugging Face model downloads |
| nlp | download,nlp | GLiNER, spaCy, Natasha |
| all | dev,download,nlp | full NLP development profile |

## Linux

```bash
./scripts/bootstrap.sh
```

Without interactive prompts:

```bash
./scripts/bootstrap.sh --profile nlp --skip-validation
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

Without interactive prompts:

```powershell
.\scripts\bootstrap.ps1 -Profile nlp -SkipValidation
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

### Model download dependencies

```bash
pip install -e .[download]
```

### NLP dependencies

```bash
pip install -e .[download,nlp]
```

### Full installation

```bash
pip install -e .[dev,api,download,nlp]
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

## NLP And Local Models

NLP is disabled by default. The base MaskFlow installation remains offline-first
and does not require ML dependencies.

Models are stored under the runtime data directory:

```text
data/models/
```

In Docker this path is mounted as `/data/models`.

Main environment variables:

```text
MASKFLOW_DEFAULT_CONFIG=configs/default.yaml
MASKFLOW_EXTRAS=download,nlp
HF_TOKEN=
MASKFLOW_NLP_ENABLED=false
MASKFLOW_NLP_AUTO_DOWNLOAD=false
MASKFLOW_GLINER_ENABLED=false
MASKFLOW_GLINER_MODEL=urchade/gliner_multi-v2.1
MASKFLOW_GLINER_MODEL_PATH=
MASKFLOW_GLINER_DEVICE=cpu
MASKFLOW_SPACY_ENABLED=false
MASKFLOW_SPACY_MODEL=ru_core_news_lg
MASKFLOW_SPACY_MODEL_PATH=
MASKFLOW_NATASHA_ENABLED=false
MASKFLOW_QWEN_ENABLED=false
MASKFLOW_QWEN_MODEL=Qwen/Qwen2.5-Coder-7B-Instruct
MASKFLOW_QWEN_MODEL_PATH=
MASKFLOW_QWEN_DEVICE=cpu
```

Environment variables override YAML only when they are explicitly present in the
process environment. Empty string values such as `MASKFLOW_GLINER_MODEL_PATH=`
are ignored, so Docker Compose can leave model paths controlled by YAML.

`MASKFLOW_DEFAULT_CONFIG` selects the YAML config used by CLI/Web/API. In Docker
you can use a config baked into the image, such as `configs/examples/nlp.yaml`,
or a file from the mounted volume, such as `/data/configs/my-config.yaml`.

`HF_TOKEN` is used by `huggingface_hub` for private/gated models and Hugging Face
API limits. Public models usually download without a token. Do not pass
`HF_TOKEN` as a Docker build arg because that can persist the secret in image
layers.

`auto_download` is disabled by default. For production, prefer preloading models
into `data/models` and setting `model_path` explicitly in YAML.

Minimal NLP section:

```yaml
nlp:
  enabled: true
  auto_download: false
  providers:
    gliner:
      enabled: true
      model_name: "urchade/gliner_multi-v2.1"
      model_path: "huggingface/urchade__gliner_multi-v2.1"
    spacy:
      enabled: true
      model_name: "ru_core_news_lg"
    natasha:
      enabled: true
    qwen:
      enabled: false
```

Prepare a model explicitly:

```bash
maskflow prepare-models --config configs/default.yaml --provider gliner --auto-download
maskflow prepare-models --config configs/default.yaml --provider spacy --auto-download
```

The command reads only NLP settings and does not require a production
`MASKFLOW_SECRET`. Without `--auto-download`, it only verifies that the model is
already available locally.
For spaCy, the model is stored under `data/models/spacy/<model_name>` instead of
being installed into the container's system Python.

For Web masking through Docker, three conditions must be true:

- the image is built with `MASKFLOW_EXTRAS=download,nlp`;
- runtime env enables `MASKFLOW_NLP_ENABLED=true` and at least one provider;
- the selected `MASKFLOW_DEFAULT_CONFIG` exists inside the container.

With `MASKFLOW_LOG_LEVEL=DEBUG`, file-processing logs should include detector
`nlp` in `detector_timings_ms`. If it is missing, the NLP pipeline was not
enabled in the config actually loaded by Web.

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

| Mode | Description | Example output |
|---|---|---|
| `hmac` | Deterministic HMAC pseudonymization. Same input always produces same token. Requires `deterministic_secret`. | `EMAIL_92af8b1c` |
| `partial` | Partial mask: email preserves domain, others keep leading/trailing chars. | `ex***@mail.ru` |
| `preserve_format` | Digit→digit, letter→letter, separators unchanged. Length is preserved. | `+7 (412) 853-91-24` |
| `redact` | Full replacement. Fast and irreversible. | `EMAIL_REDACTED` |

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

With NLP dependencies:

```bash
docker build \
  --build-arg MASKFLOW_EXTRAS=download,nlp \
  -f docker/Dockerfile \
  -t maskflow:nlp .
```

For `docker compose`, set in `.env`, then rebuild the container:

```text
MASKFLOW_DEFAULT_CONFIG=configs/examples/nlp.yaml
MASKFLOW_EXTRAS=download,nlp
HF_TOKEN=hf_...
MASKFLOW_NLP_ENABLED=true
MASKFLOW_NLP_AUTO_DOWNLOAD=true
MASKFLOW_GLINER_ENABLED=true
```

For a custom runtime config, place the file under `data/configs`, then use the
container path:

```text
MASKFLOW_DEFAULT_CONFIG=/data/configs/my-config.yaml
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
./scripts/bootstrap.sh --profile dev
./scripts/check.sh
```

## Windows

```powershell
.\scripts\bootstrap.ps1 -Profile dev
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

## Completed

- ✅ `partial` masking mode;
- ✅ `preserve_format` masking mode;
- ✅ `redact` masking mode;
- ✅ LOG processor with structural element protection;
- ✅ Plugin SHA-256 hash verification warning;
- ✅ Demasking performance: O(N) single-pass via regex alternation;
- ✅ Hard limit for JSON files >100 MB.

## Planned

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
