import os, sys, cgi, sys, occam, time, string, traceback, pickle, re

class JobControl:
	def showJobs(self, formFields):
		# Kill job if requested
		pid = formFields.get("pid", 0)
		if pid <> 0:
			try:
				procfd = os.popen("ps -o pid,command")
				procstat = procfd.read()
				procs = string.split(procstat, '\n');
				for proc in procs:
					if string.find(proc, "occam") >= 0:
						fields = re.split("[ \t]+", proc, 2)
						if int(fields[0]) == int(pid):
							os.system('kill -9 %d' % (int(pid)))
							print "<b>Job " + pid + " killed!</b><p>"
							break
			except Exception, inst:
				print "<b>Exception of type ", type(inst), ": kill of ", pid, " failed</b><p>"
			except:
				print "<b>Kill of " + pid + " failed</b><p>"
			

		# Show active occam-related jobs
		print "<b>Active Jobs</b><p>"
		print "<table class='form'>"
		print "<tr><td><b>Process</b></td><td><b>Start Time</b></td><td><b>Elapsed Time</b></td><td><b>%CPU</b></td><td><b>%Mem</b></td><td><b>Command</b></td><td> </td></tr>"
		procfd = os.popen("ps -o pid,lstart,etime,pcpu,pmem,command")
		procstat = procfd.read()
		procs = string.split(procstat, '\n');
		for proc in procs:
			if string.find(proc, "occam") >= 0:
				fields = re.split("[ \t]+", proc, 9)
				cmds = string.split(fields[-1], ' ')
				if len(cmds) < 3:
					continue
				del fields[-1]
				fields[1] = " ".join(fields[1:4]) + " " + fields[5] + "<br>" + fields[4]
				del fields[2:6]
				print "<tr>"
				for n in range(0, len(fields)):
					print "<td>", fields[n], "</td>"
				command = ""
				if len(cmds) == 3:
					command = cmds[1] + " " + string.split(cmds[2], '/')[-1][0:-12] + ".ctl"
				if len(cmds) == 4:
					command = cmds[1] + " " + cmds[2] + "<br>" + cmds[3]
				if len(cmds) == 5:
					command = cmds[1] + " " + cmds[2] + "<br>" + cmds[3] + '<br>\nSubject: "' + cmds[4].decode("hex") + '"'
				if len(cmds) == 6:
					command = cmds[1] + " " + cmds[2] + " " + cmds[4] + "<br>" + cmds[5]
				if len(cmds) == 7:
					command = cmds[1] + " " + cmds[2] + " " + cmds[4] + "<br>" + cmds[5] + '<br>\nSubject: "' + cmds[6].decode("hex") + '"'
				print "<td>", command, "</td>"
				print '<td><a href="weboccam.cgi?action=jobcontrol&pid=' + fields[1] + '">kill</a></td>'
				print "</tr>"
		print "</table>"
