import logging

logger = logging.getLogger("uvicorn.error")


async def generate_meta_diagram() -> str:
    """
    Queries Neo4j schema visualization and generates a Mermaid.js graph diagram string.

    This function fetches live metadata regarding node labels and relations,
    formatting the output directly into a Mermaid Markdown block.

    Returns:
        str: Markdown string containing the Mermaid diagram.
    """
    from src.backend.app.database.connection import driver

    query = "CALL db.schema.visualization()"
    nodes_definitions = set()
    relationships_definitions = set()

    try:
        # Zamiast 'with', tworzymy sesję i zamykamy ją ręcznie
        session = driver.session()
        try:
            result = await session.run(query)
            # Fetch all records as a list since 'result' is async
            records = [record async for record in result]
            for record in records:
                for node in record["nodes"]:
                    label = list(node.labels)[0]
                    nodes_definitions.add(f'    {label}["({label})"]')
                for rel in record["relationships"]:
                    start_label = list(rel.start_node.labels)[0]
                    end_label = list(rel.end_node.labels)[0]
                    rel_type = rel.type
                    relationships_definitions.add(f"    {start_label} -->|{rel_type}| {end_label}")
        finally:
            await session.close()

        # Build Markdown output
        mermaid_lines = ["", "```mermaid", "graph TD"]
        mermaid_lines.extend(sorted(list(nodes_definitions)))
        mermaid_lines.extend(sorted(list(relationships_definitions)))
        mermaid_lines.append("```")
        mermaid_lines.append("")

        return "\n".join(mermaid_lines)

    except Exception as e:
        logger.error(f"Failed to generate schema diagram: {e}")
        return f"\n*Failed to generate schema diagram: {e}*\n"


async def generate_meta_constraints() -> str:
    """
    Fetches all active database constraints from Neo4j and formats them into a Markdown table.

    Returns:
        str: Markdown table containing constraint details.
    """
    from src.backend.app.database.connection import driver

    query = "SHOW CONSTRAINTS"
    table_lines = [
        "",
        "| Name | Type | Entity | Properties | State |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]

    try:
        session = driver.session()
        try:
            result = await session.run(query)
            records = [record async for record in result]

            if not records:
                return "\n*No active constraints found in the database.*\n"

            for record in records:
                name = record.get("name", "N/A")
                c_type = record.get("type", "N/A")
                entity = record.get("entityType", "N/A")
                labels = ", ".join(record.get("labelsOrTypes", []))
                properties = ", ".join(record.get("properties", []))
                status = record.get("status", "ENABLED")

                table_lines.append(f"| {name} | {c_type} | {entity}(:{labels}) | {properties} | {status} |")
        finally:
            await session.close()

        table_lines.append("")
        return "\n".join(table_lines)

    except Exception as e:
        logger.error(f"Failed to retrieve database constraints: {e}")
        return f"\n*Failed to retrieve database constraints: {e}*\n"
