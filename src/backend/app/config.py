import os


class Settings:
    def __init__(self):
        self.NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.NEO4J_USER = os.getenv("NEO4J_USER", "testuser")
        self.NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "testpassword")

        if not self.NEO4J_USER or not self.NEO4J_PASSWORD:
            raise RuntimeError("Missing Neo4j credentials in environment variables")


settings = Settings()
