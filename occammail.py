#! python

# Occammail.py - send occam output as a multipart mime message
# arguments:
# 1 addressee
# 2 filename

import sys, os, string, smtplib, mimetools, MimeWriter, cStringIO

def sendMessage(toaddr, msg):
	server = smtplib.SMTP('mailhost.pdx.edu')
	server.sendmail('occam-feedback@lists.pdx.edu', toaddr, msg)
	server.quit()

def buildMessage(infile, filename):
	outfd = cStringIO.StringIO()
	writer = MimeWriter.MimeWriter(outfd)
	writer.addheader('Subject', 'Occam Results')
	writer.flushheaders();
	writer.startmultipartbody('mixed')
	writer.flushheaders()
	subpart = writer.nextpart()
	pout = subpart.startbody('application/octet-stream', 
		[('name', filename)])
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
msg = buildMessage(sys.stdin, filename)
sendMessage(toaddr, msg)

