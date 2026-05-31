import os

from src.backend.app.database.meta import (
    generate_meta_constraints,
    generate_meta_diagram,
)


def main():
    """Generates the static Markdown file for database documentation."""
    # Ensure the target documentation directory exists
    os.makedirs("docs", exist_ok=True)

    diagram = generate_meta_diagram()
    constraints = generate_meta_constraints()

    content = f"""# Database Architecture & Schema

## Current Graph Schema
{diagram}

---

## Active Constraints and Indexes
{constraints}
"""

    with open("docs/database.md", "w", encoding="utf-8") as f:
        f.write(content)

    print("Successfully generated docs/database.md")


if __name__ == "__main__":
    main()
