#dependencies:
# python-gsmmodem-new : https://github.com/babca/python-gsmmodem

from __future__ import print_function

import logging

import os

import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

from gsmmodem.modem import GsmModem

gmail_user = 'your_email@gmail.com'
gmail_password = 'your_password'

sent_from = gmail_user
to = ['recipient@gmail.com']


PORT = '/dev/ttyACM0' #check what dev your modem is
BAUDRATE = 9600
PIN = None # SIM card PIN (if any)

def send_mail(send_from, send_to, subject, text, files=None,
              server="smtp.gmail.com"):
    assert isinstance(send_to, list)

    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

    for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        msg.attach(part)


    smtp = smtplib.SMTP_SSL(server, 465)
    smtp.ehlo()
    smtp.login(gmail_user, gmail_password)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()

def handleSms(sms):
    print(u'== SMS message received ==\nFrom: {0}\nTime: {1}\nMessage:\n{2}\n'.format(sms.number, sms.time, sms.text))

    if len(sms.text) > 10:
        with open("/root/invoices.txt", "a") as file:
            file.write(sms.text + "\n")
        send_mail(sent_from, to, "Inserted New Job", "A new job has been inserted into the invoice: " + sms.text, ["/root/invoices.txt"])
        return

    if "check" in sms.text.replace(" ", "") or "Check" in sms.text.replace(" ", ""):
	send_mail(sent_from, to, "Check Current Invoice", "The current invoice is attached in this email", ["/root/invoices.txt"])
    elif "finish" in sms.text.replace(" ", "") or "Finish" in sms.text.replace(" ", ""):
        send_mail(sent_from, to, "Final Invoice", "Final invoice for this month", ["/root/invoices.txt"])
	file = open("/root/invoices.txt", 'w')
        file.write("Invoices\n")
        file.close()
    elif "delete" in sms.text.replace(" ", "") or "Delete" in sms.text.replace(" ", ""):
        with open("/root/invoices.txt", "r+") as file:
            file.seek(0, os.SEEK_END)
            pos = file.tell() - 1
            while pos > 0 and file.read(1) != "\n":
                pos -= 1
                file.seek(pos, os.SEEK_SET)
            if pos > 0:
                file.seek(pos, os.SEEK_SET)
                file.truncate()
        send_mail(sent_from, to, "Last Job Deleted", "The last job sent has been deleted")
    #send_mail(sent_from, to, "confirming SMS", sms.text)

def main():
    print('Initializing modem...')
    # Uncomment the following line to see what the modem is doing:
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    modem = GsmModem(PORT, BAUDRATE, smsReceivedCallbackFunc=handleSms)
    modem.smsTextMode = False 
    modem.connect(PIN)
    print('Waiting for SMS message...')    
    try:    
        modem.rxThread.join(2**31) # Specify a (huge) timeout so that it essentially blocks indefinitely, but still receives CTRL+C interrupt signal
    finally:
        modem.close();

if __name__ == '__main__':
    main()
