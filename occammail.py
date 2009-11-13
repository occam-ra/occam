#! python

# Occammail.py - send occam output as a multipart mime message
# arguments:
# 1 addressee
# 2 filename
# 3 optional subject line addendum

import sys, os, string, smtplib, mimetools, MimeWriter, cStringIO
import socket

def sendMessage(toaddr, msg):
	server = smtplib.SMTP('mailhost.pdx.edu')
	server.sendmail('occam-feedback@lists.pdx.edu', toaddr, msg)
	server.quit()

def buildMessage(infile, filename):
	outfd = cStringIO.StringIO()
	writer = MimeWriter.MimeWriter(outfd)
	if emailSubject != "":
	    writer.addheader('Subject', 'Occam Results: ' + emailSubject)
	else:
	    writer.addheader('Subject', 'Occam Results: ' + filename)
	writer.flushheaders();
	writer.startmultipartbody('mixed')
	writer.flushheaders()
	subpart = writer.nextpart()
	pout = subpart.startbody('text/plain')
	pout.write('Occam result file ' + filename + ' is attached.\n')
	pout.write('Sent from server ' + socket.gethostname() + '.\n')
	subpart = writer.nextpart()
	pout = subpart.startbody('application/octet-stream', [('name', filename)])
	line = infile.readline()
	while line:
		pout.write(line)
		line = infile.readline()
	writer.lastpart()
	msg = outfd.getvalue()
	outfd.close()
	return msg

toaddr = sys.argv[1]
filename = sys.argv[2]
emailSubject = sys.argv[3].decode("hex")
msg = buildMessage(sys.stdin, filename)
sendMessage(toaddr, msg)

