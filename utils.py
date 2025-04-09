
from datetime import datetime, timedelta
from ics import Calendar, Event

def generate_ical_event(title, start_time_str, end_time_str):
    c = Calendar()
    e = Event()
    e.name = title
    e.begin = start_time_str
    e.end = end_time_str
    c.events.add(e)
    return str(c).encode("utf-8")

def login_and_book_course(username, password, course_name, date_str, course_hour):
    # TODO: simulate login, scrape calendar, match time, and book if available
    # Here we mock a successful booking
    start = datetime.strptime(f"{date_str} {course_hour}:00", "%Y-%m-%d %H:%M")
    end = start + timedelta(hours=1)
    return {
        "status": "success",
        "course_title": f"{course_name} - {start.strftime('%A %H:%M')}",
        "start": start.isoformat(),
        "end": end.isoformat()
    }
