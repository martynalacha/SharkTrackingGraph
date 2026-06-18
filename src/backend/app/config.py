import os


class Settings:
    def __init__(self):
        self.NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.NEO4J_USER: str = os.getenv("NEO4J_USER")
        self.NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD")

        if not self.NEO4J_USER or not self.NEO4J_PASSWORD:
            raise RuntimeError("Missing Neo4j credentials in environment variables")


settings = Settings()
