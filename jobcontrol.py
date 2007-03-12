import os, sys, cgi, sys, occam,time, string, traceback, pickle, re
fieldIDs = [1,2,4,6,7]
class JobControl:
	def showJobs(self, formFields):
		# Kill job if requested
		pid = formFields.get("pid", 0)
		if pid <> 0:
			try:
				while 1:
					os.kill(int(pid), signal.SIGKILL)
					print "<b>Job " + pid + " killed!</b><p>"
			except Exception, e:
				print "<b>", e.args[1], ": kill of ", pid, " failed</b><p>"
			except:
				print "<b>Kill of " + pid + " failed</b><p>"
			

		# Show active occam-related jobs
		print "<b>Active Jobs</b><p>"
		print "<table>"
		procfd = os.popen("ps -f")
		procstat = procfd.read()
		procs = string.split(procstat, '\n');
		for proc in procs:
			if string.find(proc, "occam") >= 0:
				print "<tr>"
				fields = re.split("[ \t]+", proc, 7)
				for fieldID in fieldIDs:
					field = fields[fieldID]
					print "<td>", field, "</td>"
				print "<td><a href=\"weboccam.cgi?action=jobcontrol&pid=" + fields[1] + "\">kill</a></td>"
				print "</tr>"
		print "</table>"

