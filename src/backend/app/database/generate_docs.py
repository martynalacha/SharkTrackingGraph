import asyncio
import json
import os
import sys

# Dynamic path injection to resolve 'backend' and 'src' modules smoothly
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.dirname(os.path.dirname(current_dir))
src_root = os.path.dirname(backend_root)

if backend_root not in sys.path:
    sys.path.insert(0, backend_root)
if src_root not in sys.path:
    sys.path.insert(0, src_root)

from src.backend.app.database.meta import (  # noqa: E402
    generate_meta_constraints,
    generate_meta_diagram,
)
from src.backend.app.main import app  # noqa: E402

# Absolute path targeting the global 'docs' directory at the root of the project
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")


def generate_openapi_schema():
    """Extracts the full OpenAPI schema from FastAPI and saves it as JSON."""
    os.makedirs(DOCS_DIR, exist_ok=True)
    schema_path = os.path.join(DOCS_DIR, "openapi.json")

    openapi_data = app.openapi()

    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(openapi_data, f, ensure_ascii=False, indent=2)

    print(f"Successfully generated {schema_path}")


async def main():
    """Generates all dynamic documentation files for the project."""
    os.makedirs(DOCS_DIR, exist_ok=True)

    diagram = await generate_meta_diagram()
    constraints = await generate_meta_constraints()

    content = f"""# Database Architecture & Schema

## Current Graph Schema

{diagram}

---

## Active Constraints and Indexes

{constraints}
"""

    database_md_path = os.path.join(DOCS_DIR, "database.md")
    with open(database_md_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully generated {database_md_path}")

    generate_openapi_schema()


if __name__ == "__main__":
    asyncio.run(main())
