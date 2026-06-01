import logging
import os

import pandas as pd

from src.backend.app.database.connection import driver
from src.backend.app.services.wiki_service import WikiService

logger = logging.getLogger("uvicorn.error")

# Base baseline zones provided by you to initialize the database
OCEARCH_ZONES: dict[str, tuple[float, float]] = {
    "30 nm off Jacksonville, Florida": (30.5, -81.3),
    "Algoa Bay, South Africa": (-33.8, 25.8),
    "Batt Reef, Australia": (-16.8, 145.8),
    "Boca Grande": (26.7, -82.3),
    "Cairns, Australia": (-16.9, 145.8),
    "Cape Cod, MA": (41.9, -70.0),
    "Corpus Christi, TX": (27.8, -97.4),
    "East of Isla Mujeres": (21.2, -86.5),
    "False Bay, South Africa": (-34.2, 18.6),
    "Fernandina Beach, FL": (30.7, -81.5),
    "Fernando de Noronha, Brazil": (-3.9, -32.4),
    "Fort Lauderdale, FL": (26.1, -80.1),
    "Fraser Island, Australia": (-25.2, 153.2),
    "Galápagos Islands, Ecuador": (-0.7, -90.5),
    "Gansbaai, South Africa": (-34.6, 19.3),
    "Gladden Spit, Belize": (16.5, -87.5),
    "Glover's Reef, Belize": (16.8, -87.8),
    "Great Barrier Reef": (-18.0, 147.0),
    "Guanacaste, Costa Rica": (10.4, -85.7),
    "Gulf Of Mexico": (25.0, -90.0),
    "Gulf Stream (Hilton Head, SC)": (32.2, -79.5),
    "Gulf Stream (Key West, FL)": (24.6, -81.0),
    "Gulf Stream (Savannah, GA)": (31.8, -79.8),
    "Henry Reef, Australia": (-17.0, 146.0),
    "Hilton Head, SC": (32.2, -80.7),
    "Ironbound Island, Nova Scotia": (44.5, -64.0),
    "Isla Mujeres, Mexico": (21.2, -86.7),
    "Islamorada, Florida": (24.9, -80.6),
    "Jacksonville, FL": (30.3, -81.7),
    "Jekyll Island, GA": (31.1, -81.4),
    "Juan Fernández Islands, Chile": (-33.6, -78.8),
    "Juno Beach, Florida, USA": (26.9, -80.1),
    "Jupiter Beach, Florida, USA": (26.9, -80.1),
    "Keewaydin Island, FL": (26.0, -81.7),
    "Kosi Bay, South Africa": (-26.9, 32.9),
    "Kyparissia Bay, Greece": (37.2, 21.6),
    "Lady Elliot Island, Australia": (-24.1, 152.7),
    "Lastre Canyon, Northern Spain": (43.7, -8.0),
    "Lighthouse Reef, Belize": (17.2, -87.5),
    "Longboat Key, FL": (27.4, -82.7),
    "Lookout Shoals (outer), North Carolina": (34.6, -76.5),
    "Lunenburg, Nova Scotia": (44.4, -64.3),
    "Mahone Bay, Nova Scotia": (44.5, -64.4),
    "Monomoy": (41.6, -70.0),
    "Montauk, NY": (41.0, -71.9),
    "Mossel Bay, South Africa": (-34.2, 22.1),
    "Nantucket, MA": (41.3, -70.1),
    "Ningaloo Reef, Australia": (-22.5, 113.8),
    "Norfolk Island": (-29.0, 167.9),
    "Norfolk Island, Australia": (-29.0, 167.9),
    "North West Island": (-23.5, 151.7),
    "Northeast Isla Mujeres, Mexico": (21.3, -86.7),
    "Off Ocracoke, North Carolina": (35.1, -76.0),
    "Offshore of FL/GA border": (30.7, -81.0),
    "Onslow Bay": (34.5, -77.0),
    "Orlando, FL": (28.5, -81.4),
    "Ostional, Costa Rica": (10.0, -85.7),
    "Padre Island National Seashore, TX": (27.0, -97.4),
    "Palmas Del Mar, Puerto Rico": (18.1, -65.8),
    "Peninsula Osa, Costa Rica": (8.5, -83.5),
    "Pinnacles, Mozambique": (-26.5, 32.9),
    "Ponta do Ouro, Mozambique": (-26.8, 32.9),
    "Port Aransas, TX": (27.8, -97.1),
    "Port Royal Sound, SC": (32.2, -80.7),
    "Puntarenas, Costa Rica": (10.0, -84.8),
    "San Diego, CA": (32.7, -117.2),
    "San Juan, Puerto Rico": (18.5, -66.1),
    "Sanibel Island, FL": (26.4, -82.1),
    "Scatarie Island, Nova Scotia": (46.0, -59.7),
    "South Maui, HI": (20.7, -156.4),
    "St. Helena Sound, SC": (32.4, -80.4),
    "St. Simon's Island, GA": (31.2, -81.4),
    "St. Simons Island, GA": (31.2, -81.4),
    "Struisbaai, South Africa": (-34.8, 20.1),
    "Wassaw National Wildlife Refuge": (31.9, -80.9),
    "Waycross, GA": (31.2, -82.4),
    "Whitsunday Islands, Australia": (-20.1, 149.0),
    "Wrightsville Beach, NC": (34.2, -77.8),
}


async def remap_telemetry_relations(df: pd.DataFrame):
    """
    Clears existing PINGED_AT relations and recalibrates them based on current OceanGrid nodes.
    """
    logger.info("Recalibrating spatial telemetry relations in Neo4j...")

    # Clean up old relations to prevent duplication or outdated spatial bindings
    clear_relations_query = "MATCH ()-[r:PINGED_AT]->() DELETE r"

    insert_pings_query = """
    UNWIND $pings AS ping
    MATCH (s:Shark {sharkId: ping.sharkId})
    MATCH (g:OceanGrid)

    // Calculate the distance on the Neo4j side using coordinates stored in the database
    WITH s, ping, g, sqrt((ping.lat - g.centerLat)^2 + (ping.lon - g.centerLon)^2) AS distance
    ORDER BY distance ASC

    // Select the absolute closest database zone node per ping log
    WITH s, ping, collect({node: g, dist: distance})[0] AS closest

    // Extract the actual node and distance into separate variables before FOREACH
    WITH s, ping, closest.node AS targetNode, closest.dist AS targetDist

    // Connect nodes directly if within 5 degrees threshold using the clean variable
    FOREACH (i IN CASE WHEN targetDist <= 5.0 THEN [1] ELSE [] END |
        CREATE (s)-[r:PINGED_AT {
            timestamp: ping.datetime,
            lat: ping.lat,
            lon: ping.lon
        }]->(targetNode)
    )
    """

    pings_payload = []
    for _, row in df.iterrows():
        pings_payload.append(
            {
                "sharkId": str(row["id"]),
                "datetime": str(row["datetime"]),
                "lat": float(row["latitude"]),
                "lon": float(row["longitude"]),
            }
        )

    with driver.session() as session:
        session.run(clear_relations_query)
        chunk_size = 5000
        for i in range(0, len(pings_payload), chunk_size):
            session.run(insert_pings_query, pings=pings_payload[i : i + chunk_size])
    logger.info("Telemetry relations updated successfully.")


async def seed_database(clean_csv_path: str):
    """
    Seeds database nodes and dynamic structural relationships from clean CSV data.
    """
    if not os.path.exists(clean_csv_path):
        return

    # Create default OceanGrid nodes in the database from your baseline dictionary
    insert_grids_query = """
    UNWIND $grids AS grid
    MERGE (g:OceanGrid {gridId: grid.name})
    SET g.name = grid.name, g.centerLat = grid.lat, g.centerLon = grid.lon
    """
    grids_payload = [{"name": k, "lat": v[0], "lon": v[1]} for k, v in OCEARCH_ZONES.items()]

    with driver.session() as session:
        session.run(insert_grids_query, grids=grids_payload)
        logger.info("Loaded baseline OceanGrid nodes into Neo4j.")

    # Process and load unique Shark nodes
    df = pd.read_csv(clean_csv_path)
    sharks_df = df[["id", "name", "gender", "species", "weight", "length"]].drop_duplicates(subset=["id"])
    sharks_list = []

    for _, row in sharks_df.iterrows():
        species_name = str(row["species"])
        image_url = await WikiService.get_species_image_url(species_name)
        sharks_list.append(
            {
                "sharkId": str(row["id"]),
                "name": str(row["name"]),
                "gender": str(row["gender"]),
                "species": species_name,
                "weight": str(row["weight"]),
                "length": str(row["length"]),
                "speciesImage": image_url,
            }
        )

    insert_sharks_query = """
    UNWIND $sharks AS shark
    MERGE (s:Shark {sharkId: shark.sharkId})
    SET s.name = shark.name, s.gender = shark.gender, s.species = shark.species,
        s.weight = shark.weight, s.length = shark.length, s.speciesImage = shark.speciesImage
    """

    with driver.session() as session:
        session.run(insert_sharks_query, sharks=sharks_list)
        logger.info("Loaded unique Shark nodes into Neo4j.")

    # Generate or update graph connections
    await remap_telemetry_relations(df)
