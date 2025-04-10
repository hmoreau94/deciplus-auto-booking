
from datetime import datetime, timedelta
from ics import Calendar, Event
from playwright.sync_api import sync_playwright

def generate_ical_event(title, start_time_str, end_time_str):
    c = Calendar()
    e = Event()
    e.name = title
    e.begin = start_time_str
    e.end = end_time_str
    c.events.add(e)
    return str(c).encode("utf-8")

def login_and_book_course(username, password, course_name, date_str, course_hour):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            page.goto("https://member-app.deciplus.pro/cfmontpellier/signIn", timeout=60000)
            page.fill('input[type="email"]', username)
            page.fill('input[type="password"]', password)
            page.click('button:has-text("Sign In")')
            page.wait_for_selector("div.timeslot", timeout=10000)

            target_date = datetime.strptime(date_str, "%Y-%m-%d")
            time_target = f"{course_hour:02d}:00"

            page.wait_for_selector("div.timeslot", timeout=10000)
            slots = page.query_selector_all("div.timeslot")
            for slot in slots:
                title_elem = slot.query_selector(".timeslot-title")
                time_elem = slot.query_selector("div span")
                if not title_elem or not time_elem:
                    continue
                title = title_elem.inner_text().strip()
                time_range = time_elem.inner_text().strip()
                if course_name.lower() in title.lower() and time_target in time_range:
                    if "Disponible" in slot.inner_text() or "Available" in slot.inner_text():
                        slot.click()
                        page.wait_for_timeout(1000)
                        submit_btn = page.query_selector('button:has-text("Réserver")')
                        if submit_btn:
                            submit_btn.click()
                            return {
                                "status": "success",
                                "course_title": title,
                                "start": f"{date_str}T{course_hour:02d}:00:00",
                                "end": f"{date_str}T{course_hour+1:02d}:00:00"
                            }
                        else:
                            return {"status": "already_reserved", "reason": "Déjà réservé"}
            return {"status": "error", "reason": "Cours introuvable ou complet"}
        finally:
            context.close()
            browser.close()
