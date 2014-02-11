#Client should store its data in a Data object

import numpy
from matplotlib import pyplot as pl


class Data:
	def __init__(self):
		self.data = []
		self.avg = 0
		self.sd = 0
		self.detected = 0
		self.n = 20
		self.wait = 5*self.n
		self.thresh1 = 4.5 #how many std deviations you must be from mean to detect a message
		self.thresh2 = 2.2
	def getN(self): #probably won't need this when I use this class
		return self.n
	def avgIsSet(self): #also probably won't need this, since size of training data will far exceed n
		return self.avg
	def setAvg(self):
		self.avg = numpy.average(self.data)
		self.sd = numpy.std(self.data)
		print "For debugging: average and sd:"
		print self.avg
		print self.sd
	def add(self, newdata):
		self.data += newdata
		if len(self.data) - self.detected >= self.wait: #only allows it to start checking again after a certain num of more samples have passed
			self.detected = False
	def alldata(self):
		return self.data
	def gotSignal(self): #Never call this before setAvg
		#dif = abs(numpy.average(numpy.abs(self.data[-self.n:])) - self.avg)
		dif = abs(numpy.max(numpy.abs(self.data[-self.n:])) - self.avg) #blinks seem to consistently reach a peak so use max instead of average
		detectiontype = 0
		if self.detected == False:
			if dif > self.thresh1*self.sd:
				detectiontype = 1
				# pl.plot(self.data)
				# pl.show()
				# exit()
			elif dif > self.thresh2*self.sd:
				#detectiontype = 2
				#This is commented out because the second type of signal needs to be a more complicated analysis than just a smaller peak value
				pass
				
			self.detected = len(self.data)
			return detectiontype
		else:
			return False
			
if __name__ == "__main__":
	d = Data()
	f = open('ML/data.txt','r')
	lines = f.readlines()
	for idx,line in enumerate(lines):
		line = int(line)
		d.add([line])
		if idx == d.getN(): #setting the average after very few samples here - in real thing should use a few seconds of training data where I just sit still
			d.setAvg()
		if d.avgIsSet and d.gotSignal():
			print "detected!!!"
			print idx