
# 🤖 Deciplus Auto Booking

Ce script automatise la réservation de tes cours CrossFit à la salle CF Montpellier.

## 📦 Installation

1. Crée un repo GitHub privé.
2. Upload les fichiers de ce projet.
3. Dans `Settings > Secrets and variables > Actions`, ajoute les secrets suivants :

| Nom                   | Valeur                       |
|----------------------|------------------------------|
| `DECIPLUS_USERNAME`  | Ton email Deciplus           |
| `DECIPLUS_PASSWORD`  | Ton mot de passe Deciplus    |
| `EMAIL_SENDER`       | Adresse email d’envoi        |
| `EMAIL_SENDER_PASSWORD` | Mot de passe ou app password |
| `SMTP_SERVER`        | smtp.gmail.com (ex)          |
| `SMTP_PORT`          | 465                          |
| `NOTIFY_EMAIL`       | Ton adresse email perso      |

## 🚀 Lancement

- Le script tourne tous les jours à 08h (heure de Paris).
- Il vérifie si un cours est dispo dans 7 jours (CrossFit 19h ou Team Wod 10h) et tente de réserver.
- En cas de succès : tu reçois un mail avec un .ics.
- En cas d’échec : tu reçois un mail avec un lien pour re-tenter.

## 🛠️ À faire

- Ajouter le vrai parsing HTML + requête POST de réservation.
