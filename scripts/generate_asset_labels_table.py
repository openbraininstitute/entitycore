"""Generate asset labels markdown table from ALLOWED_ASSET_LABELS_PER_ENTITY."""

import pathlib

import click

from app.db.types import ALLOWED_ASSET_LABELS_PER_ENTITY, CONTENT_TYPE_TO_SUFFIX


def generate_markdown_table() -> str:
    """Generate markdown table from ALLOWED_ASSET_LABELS_PER_ENTITY."""
    # Collect all data first to calculate column widths
    data = []

    for entity_type, labels_dict in ALLOWED_ASSET_LABELS_PER_ENTITY.items():
        if labels_dict is None:
            # Ignore entries without requirements
            continue

        for asset_label, requirements_list in labels_dict.items():
            first_row = True

            for requirements in requirements_list:
                content_type = requirements.content_type

                # Determine content type string and suffix
                if content_type is None:
                    content_type_str = "N/A"
                    suffix = "N/A (directory)"
                else:
                    content_type_str = content_type.value
                    suffixes = CONTENT_TYPE_TO_SUFFIX.get(content_type, ())
                    suffix = ", ".join(suffixes)

                # Entity type column (only for first row of each asset label)
                entity_col = entity_type.value if first_row else ""

                description = requirements.description
                data.append((entity_col, asset_label.value, content_type_str, suffix, description))
                first_row = False

    # Calculate column widths dynamically
    headers = ("Type", "Value", "Content-Type", "Suffix", "Description")
    widths = [len(header) for header in headers]

    for row in data:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    # Generate table
    header_row = "| " + " | ".join(f"{headers[i]:<{widths[i]}}" for i in range(len(headers))) + " |"
    separator_row = "| " + " | ".join("-" * width for width in widths) + " |"

    rows = [header_row, separator_row]
    for row in data:
        formatted_row = "| " + " | ".join(f"{row[i]:<{widths[i]}}" for i in range(len(row))) + " |"
        rows.append(formatted_row)

    # Add header comment
    comment = [
        "<!-- This file is auto-generated from app/db/types.py -->",
        "<!-- Do not edit manually. Run 'make generate-asset-labels' to update -->",
        ""
    ]
    
    return "\n".join(comment + rows)


@click.command()
@click.option("--output", "-o", help="Output file path")
def main(output: str | None) -> None:
    """Generate asset labels markdown table."""
    table = generate_markdown_table()
    if output:
        pathlib.Path(output).write_text(table + "\n", encoding="utf-8")
        click.echo(f"Generated asset labels table written to {output}")
    else:
        click.echo(table)


if __name__ == "__main__":
    main()
