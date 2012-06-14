import os, sys, cgi, sys, occam, time, string, traceback, pickle, re
fieldIDs = [1, 4, 6, 7]
class JobControl:
	def showJobs(self, formFields):
		# Kill job if requested
		pid = formFields.get("pid", 0)
		if pid <> 0:
			try:
				os.system('kill -9 %d' % (int(pid)))
				print "<b>Job " + pid + " killed!</b><p>"
			except Exception, inst:
				print "<b>Exception of type ", type(inst), ": kill of ", pid, " failed</b><p>"
			except:
				print "<b>Kill of " + pid + " failed</b><p>"
			

		# Show active occam-related jobs
		print "<b>Active Jobs</b><p>"
		print "<table class='form'>"
		print "<tr><td>Process</td><td>Start Time</td><td>CPU Time</td><td>Command</td></tr>"
		procfd = os.popen("ps -f")
		procstat = procfd.read()
		procs = string.split(procstat, '\n');
		for proc in procs:
			if string.find(proc, "occam") >= 0:
				fields = re.split("[ \t]+", proc, 7)
				command = string.split(fields[7], ' ')
				if len(command) < 3:
					continue
				if len(command) == 5:
					command[4] = command[4].decode("hex")
				print "<tr>"
				for fieldID in fieldIDs:
					field = fields[fieldID]
					print "<td>", field, "</td>"
				print "<td>",
				for item in range(1,len(command)):
					print command[item],
				print "</td>"
				print '<td><a href="weboccam.cgi?action=jobcontrol&pid=' + fields[1] + '">kill</a></td>'
				print "</tr>"
		print "</table>"

