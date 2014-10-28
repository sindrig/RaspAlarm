#!/usr/bin/env python
import datetime
import sys
import sqlite3
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
import os

import grapher

def send_email(lines, recv='sindrigudmundsson@gmail.com', att=None):
    import smtplib

    gmail_user = "sindrigudmundsson@gmail.com"
    gmail_pwd = "gudmundsson88"
    FROM = 'sindrigudmundsson@gmail.com'
    TO = [recv] #must be a list
    SUBJECT = "New temperature list"

    # Prepare actual message
    message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO), SUBJECT, '\n'.join(lines))
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587) #or port 465 doesn't seem to work!
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(FROM, TO, message)
        server.close()
        print 'successfully sent the mail'
        return True
    except Exception:
        import traceback; traceback.print_exc()
        print "failed to send mail"
        return False

def mail(lines, att=None):
    gmail_user = "sindrigudmundsson@gmail.com"
    gmail_pwd = "gudmundsson88"
    recv = [
        'sindrigudmundsson@gmail.com',
        'kjartandige@gmail.com'
    ]

    msg = MIMEMultipart()

    text = '\n'.join(lines)

    msg['From'] = gmail_user
    #msg['To'] = recv
    msg['Subject'] = 'New temperature list'

    msg.attach(MIMEText(text))

    part = MIMEBase('application', 'octet-stream')
    with open(att, 'rb') as f:
        part.set_payload(f.read())
      
    Encoders.encode_base64(part)
    part.add_header(
        'Content-Disposition',
        'attachment; filename="%s"' % os.path.basename(att))
    msg.attach(part)

    mailServer = smtplib.SMTP("smtp.gmail.com", 587)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(gmail_user, gmail_pwd)
    mailServer.sendmail(gmail_user, recv, msg.as_string())
    # Should be mailServer.quit(), but that crashes...
    mailServer.close()
    return True

def send_temps(only_sent=1):
    with sqlite3.connect('/home/pi/tempgauge/temp.db') as conn:
        cursor = conn.cursor()
        if only_sent:
            cursor.execute('select id, timestamp, temp from temps where sent=0')
        else:
            cursor.execute('select id, timestamp, temp from temps')
        data = cursor.fetchall()
        lines = []
        x = []
        y = []
        for id, timestamp, temp in data:
            lines.append(';'.join([timestamp, '%0.3f' % temp]))
            x.append(datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S'))
            y.append(temp)
        if not lines:
            return
        if only_sent and len(lines) < 100:
            # Sendum bara ef fleiri en 100 punktar
            return
        fn = grapher.create(x, y)
        if mail(lines, att=fn):
            sql = 'update temps set sent=1 where id in ({seq})'.format(seq=','.join(['?']*len(data)))
            cursor.execute(sql, tuple([d[0] for d in data]))
            conn.commit()
        
         

if __name__ == '__main__':
    send_temps(sys.argv[-1] != 'all')
