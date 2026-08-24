"""
API Flask du jeu Tetris.
- Sert la page du jeu (templates/index.html)
- Expose une API de scores adossee a PostgreSQL

Variables d'environnement attendues (voir docker-compose.yml) :
  DB_HOST, DB_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
"""
import os
import time

import psycopg2
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "db"),
    "port": os.environ.get("DB_PORT", "5432"),
    "dbname": os.environ.get("POSTGRES_DB", "tetris"),
    "user": os.environ.get("POSTGRES_USER", "tetris"),
    "password": os.environ.get("POSTGRES_PASSWORD", "tetris"),
}


def get_connection(retries=10, delay=2):
    """
    Le conteneur 'app' peut demarrer avant que Postgres soit pret a
    accepter des connexions (depends_on ne garantit que l'ORDRE de
    demarrage, pas la disponibilite du service). On retente donc la
    connexion quelques secondes avant d'abandonner.
    """
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            return psycopg2.connect(**DB_CONFIG)
        except psycopg2.OperationalError as exc:
            last_error = exc
            print(f"[db] tentative {attempt}/{retries} echouee, nouvel essai dans {delay}s")
            time.sleep(delay)
    raise last_error


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/scores", methods=["GET"])
def list_scores():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT username, score FROM scores ORDER BY score DESC, created_at ASC LIMIT 10"
        )
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()
    return jsonify([{"username": r[0], "score": r[1]} for r in rows])


@app.route("/api/scores", methods=["POST"])
def add_score():
    data = request.get_json(force=True, silent=True) or {}
    username = str(data.get("username") or "ANONYME").strip()[:20] or "ANONYME"
    try:
        score = int(data.get("score", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "score invalide"}), 400

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO scores (username, score) VALUES (%s, %s)",
            (username, score),
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()
    return jsonify({"status": "ok"}), 201


@app.route("/healthz")
def healthz():
    return jsonify({"status": "up"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
