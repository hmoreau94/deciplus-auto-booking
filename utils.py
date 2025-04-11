from datetime import datetime, timedelta
from ics import Calendar, Event
from playwright.sync_api import sync_playwright
import calendar
import os


##############################
# 1. Gestion de l'ICal Event #
##############################

def generate_ical_event(title, start_time_str, end_time_str):
    """
    Génère une invitation iCal à partir d'un titre, d'une date de début et de fin.
    Retourne le fichier iCal encodé en bytes.
    """
    c = Calendar()
    e = Event()
    e.name = title
    e.begin = start_time_str
    e.end = end_time_str
    c.events.add(e)
    return str(c).encode("utf-8")

######################################
# 2. Gestion du Sticky Header/Colonne #
######################################

def get_target_header_bb(page, target_date):
    """
    Parcourt les blocs du sticky header et retourne la bounding box
    du header dont le span avec classe "text-primary" correspond au jour cible.
    """
    headers = page.locator("div.stickyheader div.header-box")
    count = headers.count()
    for i in range(count):
        header = headers.nth(i)
        try:
            day_text = header.locator("span.text-primary").inner_text().strip()
            if day_text.isdigit() and int(day_text) == target_date.day:
                bb = header.bounding_box()
                print(f"[DEBUG] Header cible trouvé : jour {day_text}, bounding box = {bb}")
                return bb
        except Exception as e:
            print(f"[DEBUG] Erreur lors de la lecture d'un header : {e}")
    print("[DEBUG] Aucun header correspondant trouvé pour le jour cible.")
    return None

def is_slot_in_header(slot, header_bb):
    """
    Vérifie si le centre horizontal du slot se trouve dans la zone définie par la bounding box du header cible.
    """
    try:
        slot_bb = slot.bounding_box()
        if slot_bb is None:
            return False
        slot_center = slot_bb["x"] + slot_bb["width"] / 2
        in_column = header_bb["x"] <= slot_center <= (header_bb["x"] + header_bb["width"])
        print(f"[DEBUG] Slot center = {slot_center:.2f}; Header x-range = {header_bb['x']:.2f} - {header_bb['x']+header_bb['width']:.2f} → {in_column}")
        return in_column
    except Exception as e:
        print(f"[DEBUG] Erreur lors de la vérification du slot dans le header : {e}")
        return False

def go_to_target_week(page, target_date):
    """
    Navigue vers la semaine contenant target_date. 
    Après chaque clic sur l'icône de semaine suivante, la fonction attend que l'état réseau soit inactif et que le header se mette à jour.
    """
    def get_current_week_header():
        try:
            header = page.locator('span.text-xl.font-bold.text-secondary').inner_text()
            print(f"[DEBUG] Semaine affichée : {header}")
            return header
        except:
            return ""
        
    def target_in_current_week(header_text, target_date):
        try:
            # Format attendu : 'April - Week of 7'
            month_str, _, day_str = header_text.partition(" - Week of ")
            month_str = month_str.strip()
            day_int = int(day_str.strip())
            month_int = list(calendar.month_name).index(month_str)
            current_year = target_date.year
            displayed_start = datetime(current_year, month_int, day_int)
            displayed_end = displayed_start + timedelta(days=6)
            print(f"[DEBUG] Semaine visible : {displayed_start.date()} → {displayed_end.date()}")
            return displayed_start <= target_date <= displayed_end
        except Exception as e:
            print(f"[DEBUG] Erreur parsing semaine : {e}")
            return False

    tries = 0
    max_tries = 6
    current_header = get_current_week_header()
    while tries < max_tries:
        if target_in_current_week(current_header, target_date):
            print("[INFO] Bonne semaine atteinte.")
            return
        print("[INFO] Passage à la semaine suivante...")
        page.locator('i.fa-chevron-right').click()
        # Attendre que la page se mette à jour
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        new_header = get_current_week_header()
        if new_header != current_header:
            current_header = new_header
        tries += 1
    raise Exception("Impossible d'afficher la bonne semaine dans le calendrier.")

#########################
# 3. Expansion des slots #
#########################

def expand_all_view_all(page):
    """
    Clique sur tous les boutons "View all" afin d'afficher tous les créneaux du calendrier.
    """
    try:
        view_all_buttons = page.locator(
            'button.ari-button.ari-button-filled.ari-button-standard.w-full.ari-button-base.w-full:has-text("View all")'
        )
        count = view_all_buttons.count()
        print(f"[DEBUG] Boutons 'View all' trouvés : {count}")
        for i in range(count):
            btn = view_all_buttons.nth(i)
            if btn.is_visible():
                btn.click()
                page.wait_for_timeout(500)
                print(f"[DEBUG] Bouton 'View all' cliqué n° {i+1}")
    except Exception as e:
        print(f"[DEBUG] Erreur lors de l'expansion des 'View all' : {e}")

#####################################
# 4. Gestion de l'action de booking #
#####################################

def handle_booking_action(page, date_str, course_name, is_saturday, title):
    """
    Gère les trois cas après avoir cliqué sur un timeslot dans le modal de réservation.
    Cas possibles :
      - "Cancel my booking" : le cours est déjà réservé.
      - "Reserve on the waiting list" : réservation effectuée sur la liste d'attente.
      - "Book" : réservation réussie.
    """
    print(f"[INFO] Créneau sélectionné : {title}")
    modal = page.locator("div.ari-modal-container")
    modal.wait_for(state="visible", timeout=10000)
    print("[DEBUG] Conteneur modal détecté.")
    
    if modal.locator('button:has-text("Cancel my booking")').count() > 0:
        print("[INFO] Bouton 'Cancel my booking' détecté dans la modal.")
        return {"status": "already_reserved", "reason": "Créneau déjà réservé pour cette date."}
    elif modal.locator('button:has-text("Reserve on the waiting list")').count() > 0:
        print("[INFO] Bouton 'Reserve on the waiting list' détecté dans la modal.")
        modal.locator('button:has-text("Reserve on the waiting list")').click()
        page.wait_for_selector("div.ari-modal-container", state="detached", timeout=5000)
        print("[INFO] Modal closed after successful booking.")
        return {"status": "waiting_list", "reason": "Réservé sur la liste d'attente pour cette date."}
    elif modal.locator('button:has-text("Book")').count() > 0:
        print("[INFO] Bouton 'Book' détecté dans la modal.")
        book_button = modal.locator('button:has-text("Book")')
        print(f"[DEBUG] Found {book_button.count()} book buttons in modal")
        try:
            book_button.click()
        except Exception as e:
            print(f"[ERROR] Failed to click Book: {e}")
            
        print("[DEBUG] Clicked the Book button")
        page.wait_for_selector("div.ari-modal-container", state="detached", timeout=5000)
        print("[INFO] Modal closed after successful booking.")
        if os.environ.get("DEBUG_MODE") == "1":
            page.pause()
        if is_saturday:
            return {"status": "success", "course_title": title, "start": f"{date_str}T10:00:00", "end": f"{date_str}T11:00:00"}
        else:
            return {"status": "success", "course_title": title, "start": f"{date_str}T19:00:00", "end": f"{date_str}T20:00:00"}
    else:
        print("[DEBUG] Aucun bouton d'action trouvé dans la modal.")
        return {"status": "error", "reason": "Aucun bouton d'action trouvé dans la modal pour ce créneau."}

#####################################
# 5. Fonction principale de réservation #
#####################################

def login_and_book_course(username, password, course_name, date_str, course_hour):
    """
    Pour les jours de semaine, recherche un timeslot "CrossFit" affichant exactement "7:00 PM - 8:00 PM" (pour éviter 7:00 AM et les essais gratuits).
    Pour le samedi, recherche un timeslot dont le titre contient "Team Wod".
    Si un header sticky est disponible, vérifie que le slot se trouve dans la bonne colonne.
    Une fois le slot sélectionné, clique dessus et délègue la gestion du résultat à handle_booking_action.
    """
    target_date = datetime.strptime(date_str, "%Y-%m-%d")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        # Utilisation de la locale en anglais pour garantir le format des horaires
        context = browser.new_context(locale="en-US")
        page = context.new_page()
        try:
            print("[INFO] Accès à la page de connexion...")
            page.goto("https://member-app.deciplus.pro/cfmontpellier/signIn", timeout=60000)
            page.wait_for_selector('input[type="email"]', timeout=15000)
            print("[INFO] Remplissage des identifiants...")
            page.fill('input[type="email"]', username)
            page.fill('input[type="password"]', password)
            print("[INFO] Clic sur le bouton de connexion via #signIn")
            page.locator('#signIn').click()
            page.wait_for_selector("div.timeslot", timeout=15000)
            
            print("[INFO] Navigation vers la bonne semaine...")
            go_to_target_week(page, target_date)
            
            print("[INFO] Expansion de tous les créneaux avec 'View all'...")
            expand_all_view_all(page)
            
            header_bb = get_target_header_bb(page, target_date)
            if header_bb:
                print("[DEBUG] Header cible trouvé pour le jour.")
            else:
                print("[DEBUG] Aucun header spécifique trouvé, on se base uniquement sur le titre et l'heure.")
            
            print("[INFO] Parcours des slots disponibles...")
            page.wait_for_selector("div.timeslot", timeout=10000)
            slots = page.query_selector_all("div.timeslot")
            is_saturday = (course_name.lower() == "team wod")
            for slot in slots:
                title_elem = slot.query_selector(".timeslot-title")
                time_elem = slot.query_selector("div span")
                if not title_elem or not time_elem:
                    continue
                title = title_elem.inner_text().strip()
                time_range = time_elem.inner_text().strip()
                print(f"[DEBUG] Slot trouvé : Titre='{title}', Heure='{time_range}'")
                
                if is_saturday:
                    if "team wod" not in title.lower():
                        print("[DEBUG] Slot ignoré : ce n'est pas Team Wod.")
                        continue
                else:
                    if ("crossfit" not in title.lower() or 
                        "7:00 pm - 8:00 pm" not in time_range.lower() or 
                        "essai gratuit" in title.lower()):
                        print("[DEBUG] Slot ignoré : critères CrossFit non respectés (7:00 PM - 8:00 PM requis et pas d'essai gratuit).")
                        continue
                
                if header_bb and not is_slot_in_header(slot, header_bb):
                    print(f"[DEBUG] Slot '{title}' ignoré (hors colonne cible).")
                    continue
                
                print(f"[INFO] Slot ciblé validé : '{title}' avec horaire '{time_range}'. Clic sur le slot.")
                slot.click()
                return handle_booking_action(page, date_str, course_name, is_saturday, title)
            
            print("[DEBUG] Aucun slot disponible correspondant aux critères trouvés.")
            return {"status": "error", "reason": "Créneau introuvable ou complet."}
        finally:
            context.close()
            browser.close()