import os, sys, cgi, sys, occam, time, string, traceback, pickle, re

class JobControl:
	def showJobs(self, formFields):
		# Kill job if requested
		pid = formFields.get("pid", 0)
		if pid <> 0:
			killed = False
			try:
				procfd = os.popen("ps -o pid,command")
				procstat = procfd.read()
				procs = string.split(procstat, '\n');
				for proc in procs:
					if string.find(proc, "occam") >= 0:
						fields = re.split("[ \t]+", proc, 2)
						if int(fields[0]) == int(pid):
							os.system('kill -9 %d' % (int(pid)))
							print "<b>Job " + pid + " killed.</b><p>"
							killed = True
							break
			except Exception, inst:
				print "<b>Exception of type ", type(inst), ": kill of ", pid, " failed.</b><p><p>"
			except:
				print "<b>Kill of " + pid + " failed.</b><p><p>"
			if not killed:
				print "<b>Kill of " + pid + " failed.</b><p><p>"
			

		# Show active occam-related jobs
		print "<b>Active Jobs</b><p>"
		print "<table class='data' width='100%'>"
		print "<tr class=em align=left><th>Process</th><th>Start Time</th><th>Elapsed Time</th><td>%CPU</th><th>%Mem</th><th width='40%'>Command</th><th> </th></tr>"
		procfd = os.popen("ps -o pid,lstart,etime,pcpu,pmem,command")
		procstat = procfd.read()
		procs = string.split(procstat, '\n');
		evenRow = False
		for proc in procs:
			if string.find(proc, "occam") >= 0:
				fields = re.split("[ \t]+", proc.lstrip(), 9)
				cmds = string.split(fields[-1], ' ')
				if len(cmds) < 2:
					continue
				del fields[-1]
				fields[1] = " ".join(fields[1:4]) + " " + fields[5] + "<br>" + fields[4]
				del fields[2:6]
				if evenRow:
					print "<tr valign='top'>"
					evenRow = False
				else:
					print "<tr class=r1 valign='top'>"
					evenRow = True
				for n in range(0, len(fields)):
					print "<td>", fields[n], "</td>"
				command = ""
				if len(cmds) == 2:
					if cmds[1] != "":
						command = string.split(cmds[1], '/')[-1]
					else:
						command = cmds[0]
				elif len(cmds) == 3:
					command = cmds[1] + " " + string.split(cmds[2], '/')[-1][0:-12] + ".ctl"
				elif len(cmds) == 4:
					command = cmds[1] + " " + cmds[2] + "<br>" + cmds[3]
				elif len(cmds) == 5:
					command = cmds[1] + " " + cmds[2] + "<br>" + cmds[3]
					if cmds[4] != "":
						 command += '<br>\nSubject: "' + cmds[4].decode("hex") + '"'
				elif len(cmds) == 6:
					command = string.split(cmds[1], '/')[-1] + " " + cmds[4] + "<br>" + cmds[5]
				elif len(cmds) == 7:
					command = string.split(cmds[1], '/')[-1] + " " + cmds[4] + "<br>" + cmds[5]
					if cmds[6] != "":
						command += '<br>\nSubject: "' + cmds[6].decode("hex") + '"'
				print "<td>", command, "</td>"
				print '<td><a href="weboccam.cgi?action=jobcontrol&pid=' + fields[0] + '">kill</a></td>'
				print "</tr>"
		print "</table>"
