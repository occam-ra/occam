# coding=utf-8
# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source
# distribution of this software for license terms.

import os
import re
import sys


class JobControl:
    def show_jobs(self, form_fields):
        # Kill job if requested
        pid = form_fields.get("pid", 0)
        if pid != 0:
            killed = False
            try:
                procfd = os.popen("ps -o pid,command")
                procstat = procfd.read()
                procs = procstat.split('\n')
                procs.pop(0)
                for proc in procs:
                    if proc.find("occam") >= 0:
                        fields = re.split("[ \t]+", proc.lstrip(), 2)
                        if fields[0] != "" and int(fields[0]) == int(pid):
                            os.kill(int(pid), 9)
                            print(f"<b>Job {pid} killed.</b><p>")
                            killed = True
                            break
            except Exception as inst:
                print(
                    f"<b>Exception of type {type(inst)}: kill of {pid} failed.</b><p><p>"
                )
                print(inst.args)
            except Exception:
                print(
                    f"<b>Kill of {pid} failed: {sys.exc_info()[0]}</b><p><p>"
                )
            if not killed:
                print(f"<b>Kill of {pid} failed.</b><p><p>")

        # Show active occam-related jobs
        print("<b>Active Jobs</b><p>")
        print("<table class='data' width='100%'>")
        print(
            "<tr class=em align=left><th>Process</th><th>Start Time</th><th>Elapsed Time</th><td>%CPU</th><th>%Mem</th><th width='40%'>Command</th><th> </th></tr>"
        )
        procfd = os.popen("ps -o pid,lstart,etime,pcpu,pmem,command")
        procstat = procfd.read()
        procs = procstat.split('\n')
        procs.pop(0)
        even_row = False
        for proc in procs:
            if proc.find("occam") >= 0:
                fields = re.split("[ \t]+", proc.lstrip(), 9)
                cmds = fields[-1].split(' ')
                if len(cmds) < 2:
                    continue
                if (
                    "[" in cmds[0]
                    or "defunct" in cmds[1]
                    or "weboccam.cgi" in cmds[1]
                    or ("weboccam.py" in cmds[1] and len(cmds) == 2)
                ):
                    continue
                fields.pop()
                fields[
                    1
                ] = f"{' '.join(fields[1:4])} {fields[5]}<br>{fields[4]}"
                del fields[2:6]
                if even_row:
                    print("<tr valign='top'>")
                    even_row = False
                else:
                    print("<tr class=r1 valign='top'>")
                    even_row = True
                for n in range(0, len(fields)):
                    print(f"<td>{fields[n]}</td>")
                command = ""
                if len(cmds) == 2:
                    if cmds[1] != "":
                        command = cmds[1].split('/')[-1]
                    else:
                        command = cmds[0]
                elif len(cmds) == 3:
                    command = f"{cmds[1]} {cmds[2].split('/')[-1][0:-12]}.ctl"
                elif len(cmds) == 4:
                    command = f"{cmds[1]} {cmds[2]}<br>{cmds[3]}"
                elif len(cmds) == 5:
                    command = f"{cmds[1]} {cmds[2]}<br>{cmds[3]}"
                    if cmds[4] != "":
                        command += f'<br>\n_subject: "{cmds[4].decode("hex")}"'
                elif len(cmds) == 6:
                    command = (
                        f"{cmds[1].split('/')[-1]} {cmds[4]}<br>{cmds[5]}"
                    )
                elif len(cmds) == 7:
                    command = (
                        f"{cmds[1].split('/')[-1]} {cmds[4]}<br>{cmds[5]}"
                    )
                    if cmds[6] != "":
                        command += f'<br>\n_subject: "{cmds[6].decode("hex")}"'
                print(f"<td>{command}</td>")
                print(
                    f'<td><a href="weboccam.cgi?action=jobcontrol&pid={fields[0]}">kill</a></td>'
                )
                print("</tr>")
        print("</table>")
