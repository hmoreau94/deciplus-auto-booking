
import os
import smtplib
import ssl
from email.message import EmailMessage
from datetime import datetime, timedelta
from utils import generate_ical_event, login_and_book_course

def send_email(subject, body, to_email, ical_attachment=None):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = os.environ['EMAIL_SENDER']
    msg['To'] = to_email
    msg.set_content(body)

    if ical_attachment:
        msg.add_attachment(
            ical_attachment,
            maintype="application",
            subtype="octet-stream",
            filename="reservation.ics"
        )

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(os.environ['SMTP_SERVER'], int(os.environ['SMTP_PORT']), context=context) as server:
        server.login(os.environ['EMAIL_SENDER'], os.environ['EMAIL_SENDER_PASSWORD'])
        server.send_message(msg)

def main():
    today = datetime.now()
    target_date = today + timedelta(days=7)
    weekday = target_date.weekday()  # 0 = Monday, 5 = Saturday

    if weekday in range(0, 5):
        course_name = "CrossFit"
        course_hour = 19
    elif weekday == 5:
        course_name = "Team Wod"
        course_hour = 10
    else:
        print("No course scheduled for Sunday.")
        return

    result = login_and_book_course(os.environ['DECIPLUS_USERNAME'],
                                   os.environ['DECIPLUS_PASSWORD'],
                                   course_name, target_date.strftime('%Y-%m-%d'), course_hour)

    if result['status'] == 'success':
        ical = generate_ical_event(result['course_title'], result['start'], result['end'])
        send_email("✅ Cours réservé avec succès", "Ton cours a bien été réservé 👊", os.environ['NOTIFY_EMAIL'], ical)
    elif result['status'] == 'already_reserved':
        send_email("ℹ️ Cours déjà réservé", "Tu avais déjà réservé ce cours.", os.environ['NOTIFY_EMAIL'])
    else:
        retry_link = "https://github.com/TON_UTILISATEUR/deciplus-auto-booking/actions/workflows/book-course.yml"  # à adapter
        send_email("❌ Échec de réservation", f"{result['reason']}

👉 [Re-tenter la réservation]({retry_link})",
                   os.environ['NOTIFY_EMAIL'])

if __name__ == "__main__":
    main()
