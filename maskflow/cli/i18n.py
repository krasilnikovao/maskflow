import locale
import os

MESSAGES = {
    "ru": {
        "app_help": "Локальный enterprise-сервис маскирования и обезличивания данных.",
        "mask_help": "Маскировать один файл с сохранением структуры данных.",
        "mask_dir_help": "Маскировать все поддерживаемые файлы в каталоге.",
        "source_file": "Исходный файл для маскирования.",
        "destination_file": "Файл, в который будет записан результат.",
        "source_dir": "Исходный каталог с файлами.",
        "destination_dir": "Каталог для сохранения замаскированных файлов.",
        "config": "Путь к YAML-конфигурации.",
        "log_level": "Уровень логирования.",
        "json_logs": "Включить JSON-логи.",
        "dry_run": "Проанализировать файл без записи результата.",
        "overwrite": "Перезаписывать файл назначения, если он уже существует.",
        "plugins_dir": "Каталог с внешними плагинами.",
        "audit_report": "Записать JSON-отчёт аудита.",
        "workers": "Количество параллельных обработчиков.",
        "report": "Записать JSON-отчёт обработки.",
        "usage": "Использование",
        "options": "Параметры",
        "commands": "Команды",
        "arguments": "Аргументы",
        "argument": "Аргумент",
        "option": "Параметр",
        "command": "Команда",
        "description": "Описание",
        "help_option": "Показать справку и выйти.",
        "mask_examples": (
            "Примеры:\n\n"
            "\n\n"
            "   maskflow mask input.json output.json\n\n"
            "   maskflow mask input.sql output.sql --config configs/default.yaml\n\n"
            "   maskflow mask input.txt output.txt --dry-run\n\n"
        ),
        "mask_dir_examples": (
            "Примеры:\n\n"
            "\n\n"
            "   maskflow mask-dir ./input ./output\n\n"
            "   maskflow mask-dir ./dumps ./masked --workers 4\n\n"
            "   maskflow mask-dir ./logs ./safe --overwrite\n\n"
        ),
    },
    "en": {
        "app_help": "Local enterprise data masking and anonymization service.",
        "mask_help": "Mask a single file while preserving data structure.",
        "mask_dir_help": "Mask all supported files in a directory.",
        "source_file": "Input file to mask.",
        "destination_file": "Output file for masked data.",
        "source_dir": "Input directory with files to mask.",
        "destination_dir": "Output directory for masked files.",
        "config": "Path to YAML config.",
        "log_level": "Logging level.",
        "json_logs": "Enable JSON logs.",
        "dry_run": "Analyze file without writing output.",
        "overwrite": "Overwrite destination file if it already exists.",
        "plugins_dir": "Directory with external plugins.",
        "audit_report": "Write JSON audit trail report.",
        "workers": "Number of parallel workers.",
        "report": "Write JSON processing report.",
        "usage": "Usage",
        "options": "Options",
        "commands": "Commands",
        "arguments": "Arguments",
        "argument": "Argument",
        "option": "Option",
        "command": "Command",
        "description": "Description",
        "help_option": "Show help and exit.",
        "mask_examples": (
            "Examples:\n\n"
            "\n\n"
            "   maskflow mask input.json output.json\n\n"
            "   maskflow mask input.sql output.sql --config configs/default.yaml\n\n"
            "   maskflow mask input.txt output.txt --dry-run\n\n"
        ),
        "mask_dir_examples": (
            "Examples:\n\n"
            "\n\n"
            "   maskflow mask-dir ./input ./output\n\n"
            "   maskflow mask-dir ./dumps ./masked --workers 4\n\n"
            "   maskflow mask-dir ./logs ./safe --overwrite\n\n"
        ),
    },
}


def current_language() -> str:
    forced = os.getenv("MASKFLOW_LANG")
    if forced:
        return _normalize_language(forced)

    candidates = [
        os.getenv("LC_ALL"),
        os.getenv("LC_MESSAGES"),
        os.getenv("LANGUAGE"),
        os.getenv("LANG"),
        locale.getlocale()[0],
        locale.getdefaultlocale()[0],
    ]

    for value in candidates:
        if value:
            return _normalize_language(value)

    return "en"


def _normalize_language(value: str) -> str:
    normalized = value.strip().lower()

    if normalized.startswith("ru") or normalized.startswith("russian"):
        return "ru"

    return "en"


def tr(key: str) -> str:
    language = current_language()
    return MESSAGES.get(language, MESSAGES["en"]).get(key, key)
