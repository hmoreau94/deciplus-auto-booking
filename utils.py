from datetime import datetime, timedelta
from ics import Calendar, Event
from playwright.sync_api import sync_playwright
import calendar

def generate_ical_event(title, start_time_str, end_time_str):
    c = Calendar()
    e = Event()
    e.name = title
    e.begin = start_time_str
    e.end = end_time_str
    c.events.add(e)
    return str(c).encode("utf-8")

def go_to_target_week(page, target_date):
    def get_current_week_header():
        try:
            header = page.locator('span.text-xl.font-bold.text-secondary').inner_text()
            print(f"[DEBUG] Semaine affichée : {header}")
            return header
        except:
            return ""

    def target_in_current_week(header_text, target_date):
        try:
            # Format attendu: 'April - Week of 7'
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
    while tries < max_tries:
        header = get_current_week_header()
        if target_in_current_week(header, target_date):
            print("[INFO] Bonne semaine atteinte.")
            return
        print("[INFO] Clic sur semaine suivante...")
        page.locator('i.fa-chevron-right').click()
        page.wait_for_timeout(1000)
        tries += 1
    raise Exception("Impossible d'afficher la bonne semaine dans le calendrier.")

def expand_all_view_all(page):
    """
    Clique sur tous les boutons "View all" pour afficher l'ensemble des créneaux.
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

def login_and_book_course(username, password, course_name, date_str, course_hour):
    """
    Pour les jours de semaine, course_name doit être "CrossFit" et on recherche le timeslot affichant "7:00" (7:00 PM).
    Pour le samedi (course_name = "Team Wod"), on recherche le timeslot avec ce titre, sans vérifier l'heure affichée.
    """
    target_date = datetime.strptime(date_str, "%Y-%m-%d")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            print("[INFO] Accès à la page de connexion...")
            page.goto("https://member-app.deciplus.pro/cfmontpellier/signIn", timeout=60000)
            page.wait_for_selector('input[type="email"]', timeout=15000)
            print("[INFO] Remplissage des identifiants...")
            page.fill('input[type="email"]', username)
            page.fill('input[type="password"]', password)
            print("[INFO] Clic sur le bouton de connexion via #signIn")
            sign_in_button = page.locator('#signIn')
            sign_in_button.click()
            page.wait_for_selector("div.timeslot", timeout=15000)
            print("[INFO] Navigation vers la bonne semaine...")
            go_to_target_week(page, target_date)
            print("[INFO] Expansion de tous les créneaux avec 'View all'...")
            expand_all_view_all(page)

            print("[INFO] Recherche du créneau ciblé...")
            page.wait_for_selector("div.timeslot", timeout=10000)
            slots = page.query_selector_all("div.timeslot")
            
            # Détermination du mode : jour de semaine (CrossFit) ou samedi (Team Wod)
            is_saturday = (course_name.lower() == "team wod")
            
            for slot in slots:
                title_elem = slot.query_selector(".timeslot-title")
                time_elem = slot.query_selector("div span")
                if not title_elem or not time_elem:
                    continue
                title = title_elem.inner_text().strip()
                time_range = time_elem.inner_text().strip()
                
                if is_saturday:
                    # Pour samedi, on se contente du titre "Team Wod"
                    if "team wod" in title.lower():
                        if "Disponible" in slot.inner_text() or "Available" in slot.inner_text():
                            slot.click()
                            page.wait_for_timeout(1000)
                            submit_btn = page.query_selector('button:has-text("Réserver")')
                            if submit_btn:
                                submit_btn.click()
                                return {
                                    "status": "success",
                                    "course_title": title,
                                    "start": f"{date_str}T10:00:00",
                                    "end": f"{date_str}T11:00:00"
                                }
                            else:
                                return {"status": "already_reserved", "reason": "Déjà réservé"}
                else:
                    # Pour les jours de semaine, on recherche le timeslot "CrossFit" affichant "7:00"
                    if "crossfit" in title.lower() and "7:00" in time_range:
                        if "Disponible" in slot.inner_text() or "Available" in slot.inner_text():
                            slot.click()
                            page.wait_for_timeout(1000)
                            submit_btn = page.query_selector('button:has-text("Réserver")')
                            if submit_btn:
                                submit_btn.click()
                                return {
                                    "status": "success",
                                    "course_title": title,
                                    "start": f"{date_str}T19:00:00",  # backend reservation en 24h (19:00)
                                    "end": f"{date_str}T20:00:00"
                                }
                            else:
                                return {"status": "already_reserved", "reason": "Déjà réservé"}
            return {"status": "error", "reason": "Cours introuvable ou complet"}
        finally:
            context.close()
            browser.close()