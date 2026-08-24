# TP Docker – Dockeriser une application web avec base de données

## Objectifs

- Écrire et comprendre un `Dockerfile` simple (une étape, une instruction = une action)
- Construire une image, l'exécuter, l'inspecter
- Orchestrer deux conteneurs avec `docker-compose` (application + base de données)
- Manipuler variables d'environnement, volume nommé, réseau applicatif

Durée indicative : 1h30 à 2h.

## Support

Un jeu Tetris (HTML/JS, canvas) enregistre les scores des joueurs. L'enregistrement passe par une API Flask qui écrit dans PostgreSQL. L'objectif du TP n'est pas le jeu lui-même : c'est un prétexte pour manipuler une stack réaliste à deux conteneurs.

## Architecture cible

```
Navigateur ── :5000 ──▶ conteneur "app"  (Python/Flask, image construite depuis app/Dockerfile)
                                │
                                │ réseau docker "tetris-net", résolution DNS par nom de service
                                ▼
                        conteneur "db"   (image officielle postgres:16-alpine)
                                │
                                ▼
                        volume nommé "db_data" (persistance des données)
```

L'application et la base tournent dans deux conteneurs séparés, démarrés et reliés par `docker-compose`. Seule l'image de l'application est construite par les stagiaires ; la base utilise l'image officielle Postgres telle quelle (cas très courant en entreprise : on ne réécrit pas le Dockerfile d'une brique qu'on ne maintient pas).

## Arborescence fournie

```
tp-docker-tetris/
├── app/
│   ├── app.py              API Flask (routes GET/POST /api/scores)
│   ├── requirements.txt    dépendances Python
│   ├── templates/index.html   le jeu (page servie par Flask)
│   ├── Dockerfile          image de l'application
│   └── .dockerignore
├── db/
│   └── init.sql            création de la table "scores" au 1er démarrage
├── docker-compose.yml
├── .env.example             modèle de variables d'environnement
└── FICHE_TP.md
```

## Prérequis

- Docker Engine + plugin Compose (`docker compose version`)
- Un terminal, un éditeur de texte
- Aucune installation locale de Python ou PostgreSQL n'est nécessaire : tout tourne en conteneur

## Étape 1 — Lecture du Dockerfile de l'application

Ouvrir `app/Dockerfile` et faire correspondre chaque instruction à son rôle :

| Instruction | Rôle |
|---|---|
| `FROM python:3.12-slim` | image de base : Python déjà installé, variante allégée |
| `WORKDIR /app` | définit le répertoire de travail dans le conteneur |
| `COPY requirements.txt .` puis `RUN pip install ...` | installe les dépendances **avant** de copier le code applicatif |
| `COPY . .` | copie le reste du code |
| `EXPOSE 5000` | documente le port écouté (n'ouvre rien tout seul) |
| `CMD ["python", "app.py"]` | commande exécutée au démarrage du conteneur |

**Question à faire réfléchir les stagiaires** : pourquoi copier `requirements.txt` et installer les dépendances *avant* de copier le reste du code, plutôt que de faire un seul `COPY . .` suivi d'un `RUN pip install` ? (réponse attendue : cache de build Docker — tant que `requirements.txt` ne change pas, le layer d'installation des dépendances est réutilisé, même si le code applicatif change).

## Étape 2 — Construire l'image manuellement

```bash
cd app
docker build -t tetris-app .
docker image ls | grep tetris-app
```

Vérifier avec `docker history tetris-app` que chaque instruction du Dockerfile correspond bien à un layer.

## Étape 3 — Variables d'environnement

```bash
cd ..
cp .env.example .env
```

Éditer `.env` et changer `POSTGRES_PASSWORD`. Ce fichier est lu automatiquement par `docker compose` et injecté dans `docker-compose.yml` via la syntaxe `${POSTGRES_PASSWORD}`.

## Étape 4 — Lancer la stack complète

```bash
docker compose up --build
```

Observer les logs : le conteneur `app` tente de se connecter à `db` et réessaie tant que Postgres n'est pas prêt (voir `get_connection()` dans `app.py`). C'est volontaire : `depends_on` garantit l'**ordre** de démarrage des conteneurs, pas la **disponibilité** du service à l'intérieur.

Ouvrir `http://localhost:5000`, jouer une partie, vérifier que le score apparaît dans le classement après une partie perdue.

## Étape 5 — Vérifier la persistance

```bash
docker exec -it tetris-db psql -U tetris -d tetris -c "SELECT * FROM scores;"
```

Arrêter puis relancer la stack :

```bash
docker compose down
docker compose up -d
```

Rejouer une partie et vérifier que les scores précédents sont toujours présents (grâce au volume nommé `db_data`). Puis tester la différence :

```bash
docker compose down -v
```

Que se passe-t-il sur les données après ce dernier `down -v` ? (réponse : le volume est supprimé, la table est recréée vide par `init.sql` au prochain démarrage).

## Pour aller plus loin (facultatif)

- Ajouter un `HEALTHCHECK` dans le Dockerfile de l'application (route `/healthz` déjà exposée)
- Remplacer la boucle de retry Python par une condition `depends_on: condition: service_healthy` côté `db` dans `docker-compose.yml`
- Passer le Dockerfile de l'application en **multi-stage** (étape de build séparée de l'étape d'exécution)
- Ajouter un utilisateur non-root (`USER`) dans le Dockerfile
- Remplacer le serveur de développement Flask (`app.run`) par `gunicorn` pour un usage en production

## Nettoyage

```bash
docker compose down -v
docker image rm tetris-app
```
