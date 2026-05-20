from pathlib import Path

import pytest

from maskflow.core.directory import build_directory_tasks


def test_build_directory_tasks_scans_supported_files_recursively(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    destination_dir = tmp_path / "destination"
    config_path = tmp_path / "config.yaml"

    nested_dir = source_dir / "nested"
    nested_dir.mkdir(parents=True)

    txt_file = source_dir / "a.txt"
    docx_file = nested_dir / "b.docx"
    ignored_file = nested_dir / "c.pdf"

    txt_file.write_text("txt", encoding="utf-8")
    docx_file.write_text("docx", encoding="utf-8")
    ignored_file.write_text("pdf", encoding="utf-8")
    config_path.write_text("config", encoding="utf-8")

    tasks = build_directory_tasks(
        source_dir=source_dir,
        destination_dir=destination_dir,
        config_path=config_path,
    )

    sources = {task.source for task in tasks}
    destinations = {task.destination for task in tasks}

    assert sources == {
        txt_file,
        docx_file,
    }

    assert destinations == {
        destination_dir / "a.txt",
        destination_dir / "nested" / "b.docx",
    }


def test_build_directory_tasks_supports_custom_extensions(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    destination_dir = tmp_path / "destination"
    config_path = tmp_path / "config.yaml"

    source_dir.mkdir()

    sql_file = source_dir / "dump.sql"
    txt_file = source_dir / "notes.txt"

    sql_file.write_text("sql", encoding="utf-8")
    txt_file.write_text("txt", encoding="utf-8")
    config_path.write_text("config", encoding="utf-8")

    tasks = build_directory_tasks(
        source_dir=source_dir,
        destination_dir=destination_dir,
        config_path=config_path,
        extensions={".sql"},
    )

    assert len(tasks) == 1
    assert tasks[0].source == sql_file
    assert tasks[0].destination == destination_dir / "dump.sql"


def test_build_directory_tasks_rejects_missing_source_dir(tmp_path: Path) -> None:
    missing_dir = tmp_path / "missing"

    with pytest.raises(FileNotFoundError):
        build_directory_tasks(
            source_dir=missing_dir,
            destination_dir=tmp_path / "destination",
            config_path=tmp_path / "config.yaml",
        )


def test_build_directory_tasks_rejects_file_as_source_dir(tmp_path: Path) -> None:
    source_file = tmp_path / "source.txt"
    source_file.write_text("content", encoding="utf-8")

    with pytest.raises(ValueError, match="Source path is not a directory"):
        build_directory_tasks(
            source_dir=source_file,
            destination_dir=tmp_path / "destination",
            config_path=tmp_path / "config.yaml",
        )
