import json
import os

from src.backend.app.database.meta import (
    generate_meta_constraints,
    generate_meta_diagram,
)
from src.backend.app.main import app


def generate_openapi_schema():
    """Extracts the full OpenAPI schema from FastAPI and saves it as JSON."""
    docs_dir = "docs"
    os.makedirs(docs_dir, exist_ok=True)
    schema_path = os.path.join(docs_dir, "openapi.json")

    # Fetch the schema generated automatically by FastAPI
    openapi_data = app.openapi()

    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(openapi_data, f, ensure_ascii=False, indent=2)

    print("Successfully generated docs/openapi.json")


def main():
    """Generates all dynamic documentation files for the project."""
    # Ensure the target documentation directory exists
    os.makedirs("docs", exist_ok=True)

    # 1. Generate Database Documentation
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

    # 2. Generate OpenAPI Schema for REST API Specification
    generate_openapi_schema()


if __name__ == "__main__":
    main()
