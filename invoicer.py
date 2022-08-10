import os
import json
import telebot
import smtplib
import shutil
import datetime
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

conf = json.loads(open('/home/invoicer/.env', 'r').read())

api_key = conf['TELEGRAM']['API_KEY']
authorized = conf['TELEGRAM']['AUTHORIZED']

gmail_user = conf['GMAIL']['USER']
gmail_password = conf['GMAIL']['PASSWORD']
server = conf['GMAIL']['SERVER']

sent_from = gmail_user
to = [gmail_user]

def send_mail(send_from, send_to, subject, text, files=None,
              server=server):
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

def handleMessage(msg):
    print(u'== message received ==\nFrom: {0}\nMessage:\n{1}\n'.format(msg.chat.id, msg.text))

    if len(msg.text) > 10:
        if msg.text.count(',') != 2:
            return "Wrong format. Try checking the ( , ) symbol"
        with open("/root/invoices.txt", "a") as file:
            file.write(msg.text + "\n")
        return "New job: " + msg.text

    if "check" in msg.text.replace(" ", "") or "Check" in msg.text.replace(" ", ""):
        return open("/root/invoices.txt", 'r').read().replace("\n", "\n\n")

    elif "finish" in msg.text.replace(" ", "") or "Finish" in msg.text.replace(" ", ""):
        #send_mail(sent_from, to, "Final Invoice", "Final invoice for this month", ["/root/invoices.txt"])
        shutil.copy("/root/invoices.txt", "/root/invoices_history")
        os.rename("/root/invoices_history/invoices.txt", "/root/invoices_history/invoices_" + str(datetime.datetime.today()).replace(" ", "") +".txt") 
        #file = open("/root/invoices.txt", 'w')
        #file.write("Invoices\n")
        #file.close()
        return "Ok, i've sent the email containing the finalized invoice to " + str(to)

    elif "delete" in msg.text.replace(" ", "") or "Delete" in msg.text.replace(" ", ""):
        with open("/root/invoices.txt", "r+") as file:
            file.seek(0, os.SEEK_END)
            pos = file.tell() - 1
            while pos > 0 and file.read(1) != "\n":
                pos -= 1
                file.seek(pos, os.SEEK_SET)
            if pos > 0:
                file.seek(pos, os.SEEK_SET)
                file.truncate()
            with open("/root/invoices.txt", "a") as file:
                file.write("\n")
        return "The last job sent has been deleted"

bot = telebot.TeleBot(api_key)

@bot.message_handler(func=lambda message: True)
def all(message):
    print(message.chat.id)
    if message.chat.id in authorized:
        status = handleMessage(message)
        if status != "":
            bot.send_message(message.chat.id, status)
        else:
            bot.send_message(message.chat.id, "Ok")

    else:
        bot.send_message(message.chat.id, "You aren't allowed here")


bot.polling()

