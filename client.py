# -*- coding: <utf-8> -*-
import socket
import time
import struct
import json
valtypes = ['delta','theta','low beta','high beta','low alpha','high alpha','low gamma','high gamma']
class Client:
	def __init__(self, host = '127.0.0.1' , port = 13854, bufsize = 4, timeout = 10):
		self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.host = host
		self.port  = port
		self.bufsize = bufsize
		self.timeout = timeout
		
		self.data = None
		
		self.connect()
	def set_data(self, data):
		self.data = data
	def connect(self, count=-1):
		flag = True
		success = False
		while flag:
			try:
				print('connect...',self.host, self.port)
				self.client.connect((self.host,self.port))
				#self.client.settimeout(self.timeout)
				success = True
				break
			except:
				count -= 1
				if count == 0:
					flag = False
				else:
					time.sleep(3)
		print "Connected to socket. Now configuring..."
		time.sleep(0.5)
		print "Authorizing device..."
		self.authJson()
		time.sleep(0.5)
		print "Configuring for raw output and JSON encoding..."
		self.configJson()
		raw_input("Please press enter when dongle turns blue.")
		time.sleep(0.5)
		print "Done connecting."
		time.sleep(0.5)
		
		return success
	def authJson(self):
		#authorize:
		msg = {"appName":"mytest", "appKey":"9f54141b4b4c567c558d3a76cb8d715cbde03096"}
		jmsg = json.dumps(msg, encoding="utf-8")
		self.client.send(jmsg)
	def configJson(self):
		msg = {"enableRawOutput": True, "format": "Json"}
		jmsg = json.dumps(msg, encoding="utf-8")
		self.client.send(jmsg)
		
	def close(self):
		self.client.close()
	def send(self, string):
		pass #will never try to send when this class is being used as an object
	def recv(self, plotting = False):
		r = self.recvJson(plotting)
		return r
	def recvBinary(self):
		alldata = self.client.recv(4096)
		sync = 0
		index = 0
		while sync < 3 and index < len(alldata):
			data = ord(alldata[index])			
			if data == 0xaa:
				sync += 1
			if sync == 2: #sync bytes were detected
				if data == 0x02:
					index += 1
					data = ord(alldata[index])
					print "Poor signal level:", data
				elif data == 0x04:
					index += 1
					data = ord(alldata[index])
					print "eSense attention:", data
				elif data == 0x05:
					index += 1
					data = ord(alldata[index])
					print "eSense meditation:", data
				elif data == 0x80:
					index += 1
					data = ord(alldata[index])
					print "Raw sensor length info:", data
					index += 1
					data = ord(alldata[index])
					print "Raw sensor value:", data
				elif data == 0x81:
					index += 1
					data = ord(alldata[index])
					print "EEG powers length info: ", data
					for i in range(0,8):
						val = struct.unpack('>f',alldata[index+1:index+5])[0]
						print "EEG", valtypes[i],"value:", val
						index += 4
			index += 1
		return 0
	def recvJson(self, plotting = False):
		if plotting:
			f = open("data.txt",'a')
		toreturn = 0
		data = self.client.recv(2048)
		data_packs = data.split('\r')
		for pack in data_packs:
			try:
				pack = json.loads(pack)
				#if pack.has_key('blinkStrength'):
				#	toreturn = 1
				if pack.has_key('rawEeg'):
					if not plotting: #need this because otherwise it overloads the computer doing both operations every iteration
						self.data.add([pack['rawEeg']])
					if plotting:
						f.write("%i\n"%(pack['rawEeg']))
			except:
				pass
		if plotting:
			f.close()
			
		return toreturn
			
if __name__ == "__main__":
	c = Client()

	while 1:
		c.recv(True) #this will store all recorded data into data.txt
		time.sleep(0.001)

		

