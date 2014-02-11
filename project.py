#Ben Deverett
#the use of deciseconds is due to the fact that the sensor checking takes on the order of centiseconds, and so we can't be sure it will be done before we re-check for tempo

from client import Client
import rtmidi
import time
from data import Data
import sys

FREESTYLE_MODE = 0
RECORD_MODE = 1

CLICK_OFF = 0
CLICK_ON = 1
KICK_OFF = 2
KICK_ON = 3
HAT_OFF = 4
HAT_ON = 5
SNARE_OFF = 6
SNARE_ON = 7
TONE_OFF = 8
TONE_ON = 9

MSG_CLICK = [CLICK_OFF, CLICK_ON]
MSG_KICK = [KICK_OFF, KICK_ON]
MSG_HAT = [HAT_OFF, HAT_ON]
MSG_SNARE = [SNARE_OFF, SNARE_ON]
MSG_TONE_ON = [TONE_ON]
MSG_TONE_OFF = [TONE_OFF]

#socket info:
host = '127.0.0.1'
port = 13854
#timing info:
dur_1 = 16 # 1/tempo in deciseconds, i.e. length of a 1/1 note, which is also a bar for the sake of this project -- MUST BE A MULTIPLE OF RESOLUTION
resolution = 16
dur_res = dur_1 / resolution #length of time between notes supported by resolution
metro_count = 4 #metronome denominator, i.e. x where the metronome goes on x'th notes
dur_met = dur_1 / metro_count #the metronome count (time b/t clicks) in deciseconds - ive chosen here to make it quarter notes
break_bars = 4 #number of bars to listen before recording again
break_time = break_bars * dur_1 #length of time of a break
rec_bars = 1 #number of bars to record
rec_time = rec_bars * dur_1 #length of time of a recording session
#midi info:
channel = 10
toneChannel = 1
tonePrgm = 81
vel_low = 32
vel_high = 64
clickNote = 37
kickNote = 36
hatNote = 42
snareNote = 38
toneNote = 64

class Project:
	def __init__(self, play_mode):
		
		self.mode = play_mode
		
		self.client = Client()
		self.client.set_data(Data())
		
		self.midiout = rtmidi.RtMidiOut()
		self.midiout.openPort(0)
		
		self.midiout.sendMessage(rtmidi.MidiMessage().programChange(toneChannel,tonePrgm))
		
		self.midiNotes = [None,None,None,None,None,None,None,None,None,None]
		self.midiNotes[CLICK_OFF] = (rtmidi.MidiMessage().noteOff(channel,clickNote))
		self.midiNotes[CLICK_ON] = (rtmidi.MidiMessage().noteOn(channel,clickNote,vel_low))
		self.midiNotes[KICK_OFF] = (rtmidi.MidiMessage().noteOff(channel,kickNote))
		self.midiNotes[KICK_ON] = (rtmidi.MidiMessage().noteOn(channel,kickNote,vel_high))
		self.midiNotes[HAT_OFF] = (rtmidi.MidiMessage().noteOff(channel,hatNote))
		self.midiNotes[HAT_ON] = (rtmidi.MidiMessage().noteOn(channel,hatNote,vel_high))
		self.midiNotes[SNARE_OFF] = (rtmidi.MidiMessage().noteOff(channel,snareNote))
		self.midiNotes[SNARE_ON] = (rtmidi.MidiMessage().noteOn(channel,snareNote,vel_high))
		self.midiNotes[TONE_OFF] = (rtmidi.MidiMessage().noteOff(toneChannel,toneNote))
		self.midiNotes[TONE_ON] = (rtmidi.MidiMessage().noteOn(toneChannel,toneNote,vel_low))
		
		self.drum_msgs = [MSG_KICK, MSG_HAT, MSG_SNARE]
		self.drum_idx = len(self.drum_msgs) - 1
		
		self.notes = []
		for i in range(0,resolution):
			self.notes.append([])
		
		self.elapsed = 0
		self.on_break = True
		self.last_switch = 0
		self.train()
		
	def train(self):
		raw_input("Press enter to begin training.")
		print "Now training. Please remain inactive for 10 seconds..."
		for i in range(100):
			self.client.recv()
			time.sleep(0.1)
		self.client.data.setAvg()
		print "Training complete."
		time.sleep(1)
	def sendMessage(self, msg):
		if len(msg) == 1:
			self.midiout.sendMessage(self.midiNotes[msg[0]])
		else:
			for m in msg:
				self.midiout.sendMessage(self.midiNotes[m])
	def checkSensor(self):
		self.client.recv()
		signaltype = self.client.data.gotSignal()
		if signaltype == 1:
			tosend = self.drum_msgs[self.drum_idx]
		elif signaltype == 2:
			tosend = MSG_HAT
			
		if signaltype != 0:
			self.sendMessage(tosend)
			if self.mode == RECORD_MODE:
				self.addNoteToLoop(tosend)
	def clearSensorBuffer(self):
		self.client.recv()
	def addNoteToLoop(self, msg):
		closest_idx = int(round(self.elapsed % dur_1) / dur_res)
		if msg not in self.notes[closest_idx]:
			self.notes[closest_idx].append(msg)
	def keepMusicalLoop(self, startTime):	
		#play all desired notes of the loop:
		if self.elapsed % dur_met == 0: #metronome note
			self.sendMessage(MSG_CLICK)
		if self.elapsed % dur_res == 0: #resolution'th notes
			idx = int((self.elapsed % dur_1) / dur_res)
			for msg in self.notes[idx]:
				self.sendMessage(msg)
	def go(self):
		self.sendMessage(MSG_CLICK) #first click
		startTime = time.time()
		self.elapsed = 0
		old_elapsed = self.elapsed
		while True:
			self.elapsed = round((time.time() - startTime) * 10) #the ten is for deciseconds, would be 100 for centiseconds, etc
			if self.elapsed != old_elapsed: #only care about decisecond accuracy (otherwise would try to send many clicks in the ms time between two centiseconds)
				old_elapsed = self.elapsed
				self.keepMusicalLoop(startTime)
				if self.mode == RECORD_MODE:
					if self.elapsed != 0 and self.on_break and self.elapsed - self.last_switch >= break_time: #switch to record mode
						self.on_break = False
						self.last_switch = self.elapsed
						self.sendMessage(MSG_TONE_ON)
						self.drum_idx += 1
						if self.drum_idx >= len(self.drum_msgs):
							self.drum_idx = 0
					elif (not self.on_break) and self.elapsed - self.last_switch >= rec_time: #switch to break mode
						self.on_break = True
						self.last_switch = self.elapsed
						self.sendMessage(MSG_TONE_OFF)
			if self.mode == FREESTYLE_MODE or (self.mode == RECORD_MODE and (not self.on_break)):
				self.checkSensor()
			self.clearSensorBuffer() #regardless of whether we want to get sensor info, it needs to keep clearing the buffer
		
			
if __name__ == '__main__':
	p = Project(0)
	p.go()