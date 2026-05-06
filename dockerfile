FROM python:3.10

WORKDIR /app

# Copier les dépendances
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du projet
COPY . .

# Commande par défaut
CMD ["python", "src/train.py"]