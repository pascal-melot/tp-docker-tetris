-- Execute automatiquement au premier demarrage du conteneur postgres
-- (monte dans /docker-entrypoint-initdb.d par docker-compose.yml)

CREATE TABLE IF NOT EXISTS scores (
    id SERIAL PRIMARY KEY,
    username VARCHAR(20) NOT NULL,
    score INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
