# --- Dockerfile multi-stage : etape de build separee de l'etape d'execution ---

# ---- Stage 1 : builder ----
# Sert uniquement a installer les dependances dans un environnement isole.
# Cette etape (et tout ce qu'elle contient) n'existe jamais dans l'image finale.
FROM python:3.12-slim AS builder

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ---- Stage 2 : runtime ----
# Repart d'une image de base neuve et ne recupere du builder que le strict
# necessaire pour executer l'application : le venv pret a l'emploi.
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY . .

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/healthz', timeout=2)" || exit 1

CMD ["python", "app.py"]

