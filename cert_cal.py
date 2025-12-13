import sslexp
import icalendar
import ipaddress
import socket
from datetime import timedelta
from flask import Flask, make_response

def add_alarm(days_before, domain):
    alarm = icalendar.Alarm()
    alarm.add('action', 'DISPLAY')
    alarm.add('description', f'{domain} expiry reminder')
    alarm.add('trigger', timedelta(days =-days_before))
    return alarm
    
def check_hostname(hostname):
    try:
        ipaddress.ip_address(hostname)
        return False
    except ValueError:
        pass

    try:
        socket.gethostbyname(hostname) 
        return True
    except socket.gaierror:
        return False

def create_certcal(expiry_data):
    cert_cal = icalendar.Calendar()
    cert_cal.add('prodid', '-//Puskar SSLEXP//')
    cert_cal.add('version', '2.0')
    for domain, expiry_date in expiry_data.items():
        event = icalendar.Event()
        event.add('summary', f'{domain} cert expires')
        event.add('dtstart', expiry_date)
        event.add('dtend', expiry_date)
        event.add('description', f'{domain} expires')
        event.add('dtstamp', expiry_date)
        event.add('uid', f'{domain}-{expiry_date.timestamp()}')
        event.add_component(add_alarm(7, domain))
        cert_cal.add_component(event)
    
    return cert_cal

flask_app = Flask("certcal")

@flask_app.route('/certcal/<domains>', methods=['GET'])

def main(domains):
    expiry_data = {}
    for domain in domains.split(','):
        if check_hostname(domain):
            try:
                expiry_info = sslexp.get_tls_expiration_date(domain)
                expiry_data[domain] = expiry_info
            except ConnectionRefusedError:
                continue

    cert_cal = create_certcal(expiry_data)
    response = make_response(cert_cal.to_ical().decode('utf-8'))
    response.headers['Content-Type'] = 'text/calendar; charset=utf-8'
    response.headers['Content-Disposition'] = 'inline; filename="certcal.ics"'
    return response


if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=8093, debug=True)