from fastapi import APIRouter, HTTPException, Query

from src.backend.app.database.connection import driver
from src.backend.app.schemas.shark import SharkCreate, SharkResponse, SharkUpdate

router = APIRouter(prefix="/api/sharks", tags=["Sharks"])


@router.get("/")
def get_sharks(species: str = Query(None, description="Filter sharks by exact species name")):
    """
    Returns a list of all sharks in the database.
    If a species query parameter is provided, filters the result by that species.
    """
    if species:
        query = """
        MATCH (s:Shark)
        WHERE toLower(s.species) = toLower($species)
        RETURN s {.*} AS shark_data
        ORDER BY s.name ASC
        """
        params = {"species": species}
    else:
        query = """
        MATCH (s:Shark)
        RETURN s {.*} AS shark_data
        ORDER BY s.name ASC
        """
        params = {}

    with driver.session() as session:
        result = session.run(query, **params)
        return [record["shark_data"] for record in result]


@router.get("/search")
def search_shark(q: str = Query(..., description="Search term matching sharkId or shark name")):
    """
    Finds a specific shark's full profile by performing a case-insensitive search
    on both its name and sharkId.
    """
    query = """
    MATCH (s:Shark)
    WHERE s.sharkId = $q OR toLower(s.name) = toLower($q)
    RETURN s {.*} AS shark_data
    """
    with driver.session() as session:
        result = session.run(query, q=q)
        record = result.single()
        if not record:
            raise HTTPException(status_code=404, detail=f"Shark with identifier '{q}' not found")
        return record["shark_data"]


@router.get("/{shark_id}/trajectory")
def get_shark_trajectory(shark_id: str):
    """
    Returns the chronological history of geographic points pinged by a specific shark,
    including zone coordinates and entity metadata for map visualization.
    """
    # Uwaga: poprawiłem właściwości r.timestamp, r.lat, r.lon oraz g.gridId
    # tak, aby odpowiadały dokładnie nazwom kluczy, które zapisały się w bazie w poprzednich krokach
    query = """
    MATCH (s:Shark {sharkId: $shark_id})-[r:PINGED_AT]->(g:OceanGrid)
    RETURN s.name AS name, s.species AS species, s.speciesImage AS image,
           r.timestamp AS timestamp, r.lat AS lat, r.lon AS lon, g.gridId AS zone
    ORDER BY r.timestamp ASC
    """
    with driver.session() as session:
        result = session.run(query, shark_id=shark_id)
        records = list(result)

        if not records:
            raise HTTPException(status_code=404, detail="Shark tracking data not found")

        trajectory = []
        for rec in records:
            trajectory.append(
                {"timestamp": rec["timestamp"], "lat": rec["lat"], "lon": rec["lon"], "zone": rec["zone"]}
            )

        return {
            "sharkId": shark_id,
            "name": records[0]["name"],
            "species": records[0]["species"],
            "image": records[0]["image"],
            "trajectory": trajectory,
        }


@router.post("/", status_code=201, response_model=SharkResponse)
def create_shark(shark: SharkCreate):
    """
    Creates a new Shark node in the database.
    """
    query = """
    CREATE (s:Shark {
        sharkId: $sharkId,
        name: $name,
        species: $species,
        gender: $gender,
        length: toFloat($length),
        weight: toFloat($weight),
        speciesImage: $speciesImage
    })
    RETURN s {.*} AS shark_data
    """
    with driver.session() as session:
        try:
            result = session.run(query, **shark.dict())
            return result.single()["shark_data"]
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e)) from e


@router.put("/{shark_id}", response_model=SharkResponse)
def update_shark(shark_id: str, shark: SharkUpdate):
    """
    Updates the properties of an existing Shark node matching the sharkId.
    """
    query = """
    MATCH (s:Shark {sharkId: $shark_id})
    SET s.name = $name,
        s.species = $species,
        s.gender = $gender,
        s.length = toFloat($length),
        s.weight = toFloat($weight),
        s.speciesImage = $speciesImage
    RETURN s {.*} AS shark_data
    """
    with driver.session() as session:
        result = session.run(query, shark_id=shark_id, **shark.dict())
        record = result.single()
        if not record:
            raise HTTPException(status_code=404, detail=f"Shark '{shark_id}' not found")
        return record["shark_data"]


@router.delete("/{shark_id}")
def delete_shark(shark_id: str):
    """
    Deletes a Shark node from the database along with all its connected relations.
    """
    query = """
    MATCH (s:Shark {sharkId: $shark_id})
    DETACH DELETE s
    RETURN count(s) AS deleted_count
    """
    with driver.session() as session:
        result = session.run(query, shark_id=shark_id)
        if result.single()["deleted_count"] == 0:
            raise HTTPException(status_code=404, detail=f"Shark '{shark_id}' not found")
        return {"detail": f"Shark '{shark_id}' and all its relations successfully deleted."}
