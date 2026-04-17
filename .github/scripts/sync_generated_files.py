from __future__ import annotations

import csv
import re
import sys
from pathlib import Path


README_SECTION_PATTERN = re.compile(r"(## 肃清列表\s*\n\n)(.*?)(\n## TODO)", re.DOTALL)
LICENSE_LIST_PATTERN = re.compile(r"((?:\d{2,}\. .*(?:\n|$))+)$", re.MULTILINE)
LICENSE_TEMPLATE_PLACEHOLDER = "{{APPENDIX_ENTRIES}}"
LICENSE_TEMPLATE_PATH = Path(".github") / "templates" / "LICENSE.template"
EXPECTED_COLUMNS = ["name", "Eng_name", "reason"]


def load_anime_items(project_root: Path) -> list[dict[str, str]]:
    anime_path = project_root / "anime.csv"
    with anime_path.open("r", encoding="utf-8", newline="") as anime_file:
        reader = csv.DictReader(anime_file)
        normalized_fieldnames = [str(field).strip() for field in (reader.fieldnames or [])]
        if normalized_fieldnames != EXPECTED_COLUMNS:
            raise ValueError("anime.csv header must be exactly: name, Eng_name, reason.")
        reader.fieldnames = normalized_fieldnames

        normalized_items: list[dict[str, str]] = []
        for index, item in enumerate(reader, start=1):
            name = str(item.get("name", "")).strip()
            eng_name = str(item.get("Eng_name", "")).strip()
            reason = str(item.get("reason", "")).strip()
            if not name:
                raise ValueError(f"anime.csv row {index} is missing a non-empty name.")
            if not eng_name:
                raise ValueError(f"anime.csv row {index} is missing a non-empty Eng_name.")

            normalized_items.append(
                {"name": name, "Eng_name": eng_name, "reason": reason}
            )

        return normalized_items


def escape_markdown_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def render_readme_table(anime_items: list[dict[str, str]]) -> str:
    lines = ["| 动画名 | 反对原因 |", "| --- | --- |"]
    for item in anime_items:
        lines.append(
            f"| {escape_markdown_cell(item['name'])} | {escape_markdown_cell(item['reason'])} |"
        )
    return "\n".join(lines)


def render_license_entries(anime_items: list[dict[str, str]]) -> str:
    return "\n".join(
        f"{index:02d}. {item['name']}" for index, item in enumerate(anime_items, start=1)
    )


def render_english_license_entries(anime_items: list[dict[str, str]]) -> str:
    return "\n".join(
        f"{index:02d}. {item['Eng_name']}" for index, item in enumerate(anime_items, start=1)
    )


def update_readme(project_root: Path, anime_items: list[dict[str, str]]) -> None:
    readme_path = project_root / "README.md"
    readme_content = readme_path.read_text(encoding="utf-8")
    updated_content, substitutions = README_SECTION_PATTERN.subn(
        lambda match: f"{match.group(1)}{render_readme_table(anime_items)}\n{match.group(3)}",
        readme_content,
        count=1,
    )
    if substitutions != 1:
        raise ValueError("Could not find the README.md 肃清列表 section.")

    readme_path.write_text(updated_content, encoding="utf-8")


def update_license_cn(project_root: Path, anime_items: list[dict[str, str]]) -> None:
    license_path = project_root / "LICENSE_CN"
    license_content = license_path.read_text(encoding="utf-8")

    # Only replace the trailing numbered appendix list so the rest of the file stays untouched.
    updated_content, substitutions = LICENSE_LIST_PATTERN.subn(
        f"{render_license_entries(anime_items)}\n",
        license_content,
        count=1,
    )
    if substitutions != 1:
        raise ValueError("Could not find the LICENSE_CN appendix entry list.")

    license_path.write_text(updated_content, encoding="utf-8")


def update_license(project_root: Path, anime_items: list[dict[str, str]]) -> None:
    license_template_path = project_root / LICENSE_TEMPLATE_PATH
    license_template = license_template_path.read_text(encoding="utf-8")
    if LICENSE_TEMPLATE_PLACEHOLDER not in license_template:
        raise ValueError(
            f"Could not find {LICENSE_TEMPLATE_PLACEHOLDER} in {license_template_path}."
        )

    rendered_license = license_template.replace(
        LICENSE_TEMPLATE_PLACEHOLDER,
        render_english_license_entries(anime_items),
        1,
    )
    (project_root / "LICENSE").write_text(
        rendered_license.rstrip("\n") + "\n",
        encoding="utf-8",
    )


def sync_project_files(project_root: Path) -> None:
    anime_items = load_anime_items(project_root)
    update_readme(project_root, anime_items)
    update_license_cn(project_root, anime_items)
    update_license(project_root, anime_items)


def main() -> int:
    project_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    sync_project_files(project_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
