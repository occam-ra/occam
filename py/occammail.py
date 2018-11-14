#! python
# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source
# distribution of this software for license terms.


# Occammail.py - send occam output as a multipart mime message
# arguments:
# 1 addressee
# 2 filename
# 3 optional subject line addendum

import sys, os, smtplib, socket
if sys.version_info < (2, 5):
    from email.MIMEText import MIMEText
    from email.MIMEMultipart import MIMEMultipart
else:
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

def sendMessage(toaddr, msg):
    server = smtplib.SMTP('mailhost.pdx.edu')
    msg['From'] = 'occam-feedback@lists.pdx.edu'
    msg['To'] = toaddr
    server.sendmail('occam-feedback@lists.pdx.edu', toaddr, msg.as_string())
    server.quit()

def buildMessage(infile, filename, emailSubject):
    msg = MIMEMultipart()
    if emailSubject != "":
        msg['Subject'] = 'OCCAM Results: ' + emailSubject
    else:
        msg['Subject'] = 'OCCAM Results: ' + filename
    email = 'OCCAM result file ' + filename + ' is attached.\n'
    email += 'Sent from server ' + socket.getfqdn()
    if ".rc.pdx.edu" in socket.getfqdn():
        email += ' for occam.oit.pdx.edu.\n'
    else:
        email += '.\n'
    emailmsg = MIMEText(email, 'plain')
    msg.attach(emailmsg)
    line = infile.readline()
    csv = line
    while line:
        csv += line
        line = infile.readline()
    csvmsg = MIMEText(csv, _subtype='csv')
    csvmsg.add_header('Content-Disposition', 'attachment', filename=filename)
    msg.attach(csvmsg)
    return msg

toaddr = sys.argv[1]
filename = sys.argv[2]
emailSubject = sys.argv[3].decode("hex")
msg = buildMessage(sys.stdin, filename, emailSubject)
sendMessage(toaddr, msg)

