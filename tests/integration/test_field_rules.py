import json
from pathlib import Path
from xml.etree import ElementTree as ET

from typer.testing import CliRunner

from maskflow.cli.app import app

runner = CliRunner()


def write_config(path: Path) -> None:
    path.write_text(
        """
pipeline:
  deterministic_secret: "secret"

rules:
  email:
    enabled: true
    mode: hmac
    prefix: EMAIL

field_rules:
  password:
    enabled: true
    action: remove

  token:
    enabled: true
    action: replace
    replacement: "[TOKEN]"

  comment:
    enabled: true
    action: mask
""",
        encoding="utf-8",
    )


def test_json_field_rules_remove_replace_and_mask(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    source = tmp_path / "source.json"
    destination = tmp_path / "masked.json"

    write_config(config)

    source.write_text(
        json.dumps(
            {
                "email": "admin@example.com",
                "password": "secret-password",
                "token": "secret-token",
                "comment": "Contact admin@example.com",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "mask",
            str(source),
            str(destination),
            "--config",
            str(config),
        ],
    )

    assert result.exit_code == 0

    payload = json.loads(destination.read_text(encoding="utf-8"))

    assert "password" not in payload
    assert payload["token"] == "[TOKEN]"
    assert payload["email"].startswith("EMAIL_")
    assert "admin@example.com" not in payload["comment"]
    assert payload["comment"].startswith("Contact EMAIL_")


def test_xml_field_rules_remove_attribute_and_replace_text(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    source = tmp_path / "source.xml"
    destination = tmp_path / "masked.xml"

    write_config(config)

    source.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<root>
  <user password="secret-password">
    <token>secret-token</token>
    <comment>Contact admin@example.com</comment>
  </user>
</root>
""",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "mask",
            str(source),
            str(destination),
            "--config",
            str(config),
        ],
    )

    assert result.exit_code == 0

    root = ET.parse(destination).getroot()
    user = root.find("user")
    token = root.find(".//token")
    comment = root.find(".//comment")

    assert user is not None
    assert "password" not in user.attrib

    assert token is not None
    assert token.text == "[TOKEN]"

    assert comment is not None
    assert comment.text is not None
    assert "admin@example.com" not in comment.text
    assert "EMAIL_" in comment.text


def test_csv_field_rules_replace_and_mask_columns(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    source = tmp_path / "source.csv"
    destination = tmp_path / "masked.csv"

    write_config(config)

    source.write_text(
        "email,password,token,comment\n"
        "admin@example.com,secret-password,secret-token,Contact admin@example.com\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "mask",
            str(source),
            str(destination),
            "--config",
            str(config),
        ],
    )

    assert result.exit_code == 0

    content = destination.read_text(encoding="utf-8")

    assert "secret-password" not in content
    assert "secret-token" not in content
    assert "[TOKEN]" in content
    assert "admin@example.com" not in content
    assert "EMAIL_" in content
