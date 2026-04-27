from __future__ import annotations

import csv
import re
import sys
from pathlib import Path


README_SECTION_PATTERN = re.compile(r"(## 肃清列表\s*\n\n)(.*?)(\n## TODO)", re.DOTALL)
LICENSE_TEMPLATE_PLACEHOLDER = "{{APPENDIX_ENTRIES}}"
LICENSE_TEMPLATE_PATH = Path(".github") / "templates" / "LICENSE.template"
LICENSE_CN_TEMPLATE_PATH = Path(".github") / "templates" / "LICENSE_CN.template"
EXPECTED_COLUMNS = ["category", "score", "name", "Eng_name", "reason"]
DEFAULT_CATEGORY = "未分类"


def load_anime_items(project_root: Path) -> list[dict[str, str]]:
    anime_path = project_root / "anime.csv"
    with anime_path.open("r", encoding="utf-8", newline="") as anime_file:
        reader = csv.DictReader(anime_file)
        normalized_fieldnames = [str(field).strip() for field in (reader.fieldnames or [])]
        if normalized_fieldnames != EXPECTED_COLUMNS:
            raise ValueError(
                "anime.csv header must be exactly: category, score, name, Eng_name, reason."
            )
        reader.fieldnames = normalized_fieldnames

        normalized_items: list[dict[str, str]] = []
        for index, item in enumerate(reader, start=1):
            category = str(item.get("category", "")).strip() or DEFAULT_CATEGORY
            score = str(item.get("score", "")).strip()
            name = str(item.get("name", "")).strip()
            eng_name = str(item.get("Eng_name", "")).strip()
            reason = str(item.get("reason", "")).strip()
            if not name:
                raise ValueError(f"anime.csv row {index} is missing a non-empty name.")
            if not eng_name:
                raise ValueError(f"anime.csv row {index} is missing a non-empty Eng_name.")

            normalized_items.append(
                {
                    "category": category,
                    "score": score,
                    "name": name,
                    "Eng_name": eng_name,
                    "reason": reason,
                }
            )

        return normalized_items


def escape_markdown_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def group_items_by_category(
    anime_items: list[dict[str, str]],
) -> dict[str, list[dict[str, str]]]:
    grouped_items: dict[str, list[dict[str, str]]] = {}
    for item in anime_items:
        grouped_items.setdefault(item["category"], []).append(item)
    return grouped_items


def render_readme_table(anime_items: list[dict[str, str]]) -> str:
    lines: list[str] = []
    for category, category_items in group_items_by_category(anime_items).items():
        lines.extend(
            [
                "<details>",
                f"<summary>{escape_markdown_cell(category)}</summary>",
                "",
                "| 序号 | 严重程度 | 番剧名 | 点评 |",
                "| --- | --- | --- | --- |",
            ]
        )
        for index, item in enumerate(category_items):
            lines.append(
                f"| {index} | {escape_markdown_cell(item['score'])} | "
                f"{escape_markdown_cell(item['name'])} | "
                f"{escape_markdown_cell(item['reason'])} |"
            )
        lines.extend(["", "</details>", ""])

    if lines:
        lines.pop()
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
    license_template_path = project_root / LICENSE_CN_TEMPLATE_PATH
    license_template = license_template_path.read_text(encoding="utf-8")
    if LICENSE_TEMPLATE_PLACEHOLDER not in license_template:
        raise ValueError(
            f"Could not find {LICENSE_TEMPLATE_PLACEHOLDER} in {license_template_path}."
        )

    rendered_license = license_template.replace(
        LICENSE_TEMPLATE_PLACEHOLDER,
        render_license_entries(anime_items),
        1,
    )
    (project_root / "LICENSE_CN").write_text(
        rendered_license.rstrip("\n") + "\n",
        encoding="utf-8",
    )


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
