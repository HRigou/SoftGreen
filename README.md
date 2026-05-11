# SoftGreen
MVP local-first pour analyse de sols/plantes avec frontend React et backend FastAPI + PostgreSQL.

## Architecture
- `frontend/`: interface React + TypeScript.
- `backend/model/`: modèle de données (MCD, entités métiers, schéma).
- `backend/thinker/`: modèles importés et pipeline IA (PyTorch).
- `backend/app/`: API FastAPI (endpoints, services, persistence).
- `backend/storage/`: fichiers runtime (uploads, runs).
- `data/dataset/`: dataset principal.
- `data/enriched/`: enrichissements analytiques générés.

## Démarrage
```bash
docker compose up --build
```

- Frontend: `http://localhost:5173`
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

## Contrat API vidéo
- `POST /api/v1/video-reports`
- input multipart: `video`, `frameIntervalSec`, `latitude`, `longitude`, `sampledAt`
- output: rapport agrégé + séries par frame + previews annotés.

## Thinker
- Service d'inférence actuel: `backend/app/services/thinker_inference.py`
- Entraînement bootstrap: `backend/thinker/train.py`
- Enrichissement dataset: `backend/thinker/scripts/enrich_dataset.py`

## Notes
- Les scores hydratation/richesse actuels sont des proxys visuels.
- Pour une fiabilité métier, brancher des modèles PyTorch supervisés avec ground-truth capteurs/labo.
