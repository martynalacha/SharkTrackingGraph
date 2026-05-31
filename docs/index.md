# Shark Tracking Graph

The project focuses on deploying a graph database system to map ocean shark migration routes using telemetry data. By leveraging native Neo4j graph processing, the system converts geographic coordinate readings into specific oceanic zones without using expensive SQL joins. This topological data enables efficient calculation of movement trajectories, behavioral patterns, and population densities across different sectors.

---

## Running the Stack

To launch the entire application stack (FastAPI backend, Vanilla JS frontend, and Neo4j graph database) in a local development environment, you only need Docker and Docker Compose installed.

### 1. Environment Configuration

Create a `.env` file in the root directory of the project and define your database credentials:

```env
# Neo4j Database Credentials (Example configuration)
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password_here
NEO4J_HOST=neo4j
NEO4J_PORT=7687

# FastAPI Environment Configuration
ENV_MODE=development

```

### 2. Launching Containers

Run the following command in your terminal to build the backend image and start all services:

```bash
docker compose up --build
```

### 3. Accessing the Application

Once the containers are fully initialized, the stack exposes the following endpoints:

* **Frontend UI & REST API:** http://localhost:8000
* **Neo4j Browser (Database GUI):** http://localhost:7474
