from dotenv import load_dotenv
load_dotenv()

import os
from datetime import datetime, timedelta
from utils import login_and_book_course, generate_ical_event

def main():
    # Calcul de la date cible dans 7 jours
    today = datetime.now()
    target_date = today + timedelta(days=7)
    weekday = target_date.weekday()  # lundi=0, samedi=5, dimanche=6

    if weekday in range(0, 5):
        course_name = "CrossFit"
        course_hour = 19  # pour les jours de semaine, réservation pour 7:00 PM (19h)
    elif weekday == 5:
        course_name = "Team Wod"
        course_hour = 10  # pour le samedi, réservation à 10h
    else:
        print("[INFO] Aucun cours programmé pour le dimanche.")
        return

    print(f"[INFO] Tentative de réservation pour '{course_name}' le {target_date.strftime('%Y-%m-%d')}.")
    
    result = login_and_book_course(
        os.environ.get("DECIPLUS_USERNAME"),
        os.environ.get("DECIPLUS_PASSWORD"),
        course_name,
        target_date.strftime("%Y-%m-%d"),
        course_hour
    )

    print("[INFO] Résultat de la réservation:")
    print(result)

    if result["status"] == "success":
        ical = generate_ical_event(result["course_title"], result["start"], result["end"])
        print("[INFO] Réservation réussie.")
        # Vous pouvez éventuellement sauvegarder le fichier ICS localement pour vérification :
        with open("reservation.ics", "wb") as f:
            f.write(ical)
        print("[INFO] Invitation iCal sauvegardée sous 'reservation.ics'.")
    elif result["status"] in ("already_reserved", "waiting_list"):
        print(f"[INFO] Réservation non effectuée : {result['reason']}")
    else:
        print(f"[ERROR] Erreur : {result.get('reason', 'Erreur inconnue')}")

if __name__ == "__main__":
    main()