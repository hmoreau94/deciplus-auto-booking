
# 🤖 Deciplus Auto Booking

Un bot Playwright pour automatiser la réservation de vos créneaux CrossFit via le site Deciplus.

## 🚀 Fonctionnalités

- Se connecte automatiquement à votre compte.
- Navigue jusqu’à la bonne semaine.
- Clique sur les bons créneaux selon vos préférences.
- Gère les cas de succès, déjà réservé ou liste d’attente.
- Peut être lancé localement ou automatiquement chaque jour avec GitHub Actions.

---

## 📦 Installation (locale)

1. **Cloner le repo**
```bash
git clone https://github.com/votre-utilisateur/deciplus-auto-booking.git
cd deciplus-auto-booking
```

2. **Installer les dépendances**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install
```

3. **Créer un fichier `.env`**
```env
DECIPLUS_USERNAME=your@email.com
DECIPLUS_PASSWORD=your_password
```

4. **Configurer les créneaux souhaités dans `config.py`**
```python
DESIRED_SLOTS = [
    {
        "activity": "CrossFit",
        "start_hour": 19,
        "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
    },
    {
        "activity": "Team Wod",
        "start_hour": 10,
        "days": ["saturday"]
    }
]
```

5. **Lancer le script**
```bash
python main.py
```

Pour du debug visuel, lance avec :
```bash
DEBUG_MODE=1 python main.py
```

---

## 🧑‍💻 Utilisation via GitHub Actions

1. **Définir vos Secrets dans le repo GitHub :**

Dans **Settings > Secrets and variables > Actions**, ajouter :

| Nom                | Description                         |
|--------------------|-------------------------------------|
| `DECIPLUS_USERNAME`| Votre email de connexion            |
| `DECIPLUS_PASSWORD`| Votre mot de passe Deciplus         |

2. **Workflow quotidien**

Le fichier `.github/workflows/book-course.yml` est pré-configuré pour tenter une réservation tous les jours à 08h (heure UTC) pour le créneau dans 7 jours.

---

## 📁 Structure

```
.
├── .github/workflows/book-course.yml     # GitHub Actions
├── config.py                             # Créneaux désirés
├── main.py                               # Script principal
├── utils.py                              # Toutes les fonctions Playwright
├── requirements.txt                      # Dépendances Python
```

---

## ✅ TODO possibles

- Envoi de mail de confirmation
- Intégration à iCal (désactivé ici)
- Interface web simple pour configurer les créneaux

---

Développé avec ❤️ pour la team CF Montpellier.
