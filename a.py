from project import Project
import sys

#args:
try:
	mode = int(sys.argv[1]) #0 for freestyle, 1 for record
except:
	print "Usage: >>a.py <mode>\n0: freestyle\n1: record"
	exit()

p = Project(mode)
p.go()