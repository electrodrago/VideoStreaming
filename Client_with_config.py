from tkinter import *
from tkinter import ttk
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os, time
import shutil

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"


class Client_with_config:
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT

	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	BACKWARD = 4
	FORWARD = 5

	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		# Added
		self.lossPacket = IntVar()
		self.lossPacket.set(0)

		self.currFrame = IntVar()
		self.currFrame.set(0)

		self.progress = IntVar()
		self.progress.set(0)

		self.test = StringVar()
		self.test.set('')

		self.lossDis = DoubleVar() # Loss rate display
		self.lossDis.set(0)

		self.startTime = 0

		self.totalData = IntVar()
		self.totalData.set(0)

		self.totalTime = IntVar()
		self.totalTime.set(0)

		self.videoDataRate = DoubleVar()
		self.videoDataRate.set(0)

		self.count = 1 # Cache storing
		self.alter = False # Check if alter the flow
		self.toggle = 0 # Check if consecutive backward or forward

		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.createWidgets()
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)  # Used
		self.rtpPort = int(rtpport)  # Used
		self.fileName = filename  # Used
		self.rtspSeq = 0  # Used
		self.sessionId = 0  # Used
		self.requestSent = -1  # Used
		self.teardownAcked = 0  # Used
		self.connectToServer()
		self.frameNbr = 0  # Used

	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI
	def createWidgets(self):
		"""Build GUI."""
		# Create Setup button
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup["fg"] = "blue"
		self.setup["bg"] = "white"
		self.setup.grid(row=3, column=0, padx=2, pady=2)

		# Create Play button
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start["fg"] = "dark green"
		self.start["bg"] = "white"
		self.start.grid(row=3, column=1, padx=2, pady=2)

		# Create Pause button
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause["fg"] = "red"
		self.pause["bg"] = "white"
		self.pause.grid(row=3, column=2, padx=2, pady=2)

		# Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Teardown"
		self.teardown["command"] = self.exitClient
		self.teardown["fg"] = "orange"
		self.teardown["bg"] = "white"
		self.teardown.grid(row=3, column=3, padx=2, pady=2)

		# Create a label to display the movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=4, sticky=W + E + N + S, padx=5, pady=5)

		# Progress bar
		self.bar = Label(self.master, anchor='w')
		self.bar["textvariable"] = self.test
		self.bar["bg"] = "white"
		self.bar["fg"] = "green"
		self.bar["justify"] = LEFT
		self.bar.grid(row=1, column=0, columnspan=4, sticky=W + E + N + S, padx=5, pady=5)


		# Button change
		# Create backward button
		self.backward = Button(self.master, width=10, padx=3, pady=3)
		self.backward["text"] = "<<"
		self.backward["command"] = self.moveBackward
		self.backward["fg"] = "red"
		self.backward["bg"] = "white"
		self.backward.grid(row=2, column=0, padx=2, pady=2)

		# Create forward button
		self.forward = Button(self.master, width=10, padx=3, pady=3)
		self.forward["text"] = ">>"
		self.forward["command"] = self.moveForward
		self.forward["fg"] = "red"
		self.forward["bg"] = "white"
		self.forward.grid(row=2, column=3, padx=2, pady=2)

		# Create another label to display the statistic
		self.label1 = Label(self.master)
		self.label1["text"] = "RTP packet loss rate:"
		self.label1.grid(row=4, column=0, sticky=W + E + N + S, padx=5, pady=5)
		self.info1 = Label(self.master, textvariable=self.lossDis)
		self.info1.grid(row=4, column=2, sticky=W + E + N + S, padx=5, pady=5)

		self.label2 = Label(self.master)
		self.label2["text"] = "Current frame number:"
		self.label2.grid(row=5, column=0, sticky=W + E + N + S, padx=5, pady=5)
		self.info2 = Label(self.master, textvariable=self.currFrame)
		self.info2.grid(row=5, column=2, sticky=W + E + N + S, padx=5, pady=5)

		self.label3 = Label(self.master)
		self.label3["text"] = "Video data rate:"
		self.label3.grid(row=6, column=0, sticky=W + E + N + S, padx=5, pady=5)
		self.info3 = Label(self.master, textvariable=self.videoDataRate)
		self.info3.grid(row=6, column=2, sticky=W + E + N + S, padx=5, pady=5)
		self.donvi3 = Label(self.master)
		self.donvi3["text"] = "Bytes/second"
		self.donvi3.grid(row=6, column=3, sticky=W + E + N + S, padx=5, pady=5)

	def setupMovie(self):
		"""Setup button handler."""
		# Send SETUP request to server, insert the Transport header
		# Read server's response and parse the Session header
		# to get RTSP session ID
		# Parse inside receive threading
		if self.state == self.INIT:
			self.sendRtspRequest(self.SETUP)
			# Make dir store cache
			try:
				os.makedirs('cache')
			except:
				print('The directory is there')

	def exitClient(self):
		"""Teardown button handler."""
		self.sendRtspRequest(self.TEARDOWN)
		self.master.destroy()
		try:
			shutil.rmtree('cache')
			# os.rmdir('cache')
		except:
			print('Directory cache is not created')

	def pauseMovie(self):
		"""Pause button handler."""
		if self.state == self.PLAYING:
			self.sendRtspRequest(self.PAUSE)

	def playMovie(self):
		"""Play button handler."""
		if self.state == self.READY:
			threading.Thread(target=self.listenRtp).start()
			self.playEvent = threading.Event()
			self.playEvent.clear()
			self.sendRtspRequest(self.PLAY)
			if self.alter:
				threading.Thread(target=self.alterDisplay).start()

	def moveForward(self):
		"""Forward button handler."""
		if self.state == self.PLAYING or self.state == self.READY:
			if not self.alter:
				self.alter = True
			else:
				self.toggle = 1

			threading.Thread(target=self.alterDisplay).start()

	def moveBackward(self):
		"""Backward button handler."""
		if self.state == self.PLAYING or self.state == self.READY:
			if not self.alter:
				self.alter = True
			else:
				self.toggle = -1

			threading.Thread(target=self.alterDisplay).start()

	def alterDisplay(self):
		# Alter threading
		while True:
			time.sleep(0.05)
			if self.toggle < 0:
				if self.currFrame.get() - 20 > 0:
					self.currFrame.set(self.currFrame.get() - 20)
				else:
					self.currFrame.set(1)
				self.toggle = 0
			elif self.toggle > 0:
				if self.currFrame.get() + 20 < self.frameNbr - 5:
					self.currFrame.set(self.currFrame.get() + 20)
				self.toggle = 0

			img_cache_location = 'cache/' + CACHE_FILE_NAME + str(self.currFrame.get()) + CACHE_FILE_EXT
			self.updateMovie(img_cache_location)
			self.currFrame.set(self.currFrame.get() + 1)

			self.progress.set(round(self.currFrame.get() / 500 * 100))
			self.test.set('|' * round(self.progress.get() * 2.05))

			if self.requestSent == self.PAUSE or self.requestSent == self.TEARDOWN or self.currFrame.get() == 501:
				break

	def listenRtp(self):
		"""Listen for RTP packets."""
		self.startTime = time.time()
		prevTime = self.totalTime.get()
		while True:
			try:
				self.totalTime.set(prevTime + int(time.time() - self.startTime))
				data = self.rtpSocket.recv(20480)
				# Check the data
				if self.totalData.get() + len(data) > self.totalData.get():
					self.totalData.set(self.totalData.get() + len(data))
					if self.totalTime.get() == 0:
						self.videoDataRate.set(0)
					else:
						self.videoDataRate.set(round(self.totalData.get() / self.totalTime.get() / 1024, 2))
				if data:
					rtpPacket = RtpPacket()
					rtpPacket.decode(data)

					# Receive the frame number and check if late packet
					if rtpPacket.seqNum() > self.frameNbr:
						self.frameNbr = rtpPacket.seqNum()
						# print('Receive packet with frame number: ' + str(rtpPacket.seqNum()))
						if not self.alter:
							self.currFrame.set(rtpPacket.seqNum())
							self.progress.set(round(rtpPacket.seqNum() / 500 * 100))
							self.test.set('|' * round(self.progress.get() * 2.05))
							self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
						else:
							self.writeFrame(rtpPacket.getPayload())
							if self.count == 501:
								break
					elif rtpPacket.seqNum() < self.frameNbr:
						# Check loss packet here
						self.lossPacket.set(self.lossPacket.get() + self.frameNbr - rtpPacket.seqNum())
						self.lossDis.set(round(self.lossPacket.get() / self.frameNbr, 2))

			except:
				print('Not receive data')
				if self.playEvent.is_set():
					break

				if self.teardownAcked == 1:
					self.rtpSocket.shutdown(socket.SHUT_RDWR)
					self.rtpSocket.close()
					break

	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
		img_cache_location = 'cache/' + CACHE_FILE_NAME + str(self.count) + CACHE_FILE_EXT
		self.count += 1
		img = open(img_cache_location, 'wb')
		img.write(data)
		img.close()
		return img_cache_location

	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
		img = Image.open(imageFile)
		frame = ImageTk.PhotoImage(img)
		img.close()
		self.label.configure(image=frame, height=288)
		self.label.image = frame

	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.rtspSocket.connect((self.serverAddr, self.serverPort))
			print('Connect RTSP')
		except:
			tkinter.messagebox.showwarning("Fail to connect to Server.py")

	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""
		# Insert the CSeq header, the value of CSeq initialize to 0
		# but start at 1
		if requestCode == self.SETUP:
			threading.Thread(target=self.recvRtspReply).start()
			self.rtspSeq = 1

			request = 'SETUP ' + self.fileName + ' RTSP/1.0'
			request += '\nCSeq: ' + str(self.rtspSeq)
			request += '\nTransport: RTP/UDP; client_port= ' + str(self.rtpPort)

			self.rtspSocket.send(request.encode())
			self.requestSent = self.SETUP

		elif requestCode == self.PLAY:
			self.rtspSeq += 1

			request = 'PLAY ' + self.fileName + ' RTSP/1.0'
			request += '\nCSeq: ' + str(self.rtspSeq)
			request += '\nSession: ' + str(self.sessionId)

			self.rtspSocket.send(request.encode())
			self.requestSent = self.PLAY

		elif requestCode == self.PAUSE:
			self.rtspSeq += 1

			request = 'PAUSE ' + self.fileName + ' RTSP/1.0'
			request += '\nCSeq: ' + str(self.rtspSeq)
			request += '\nSession: ' + str(self.sessionId)

			self.rtspSocket.send(request.encode())
			self.requestSent = self.PAUSE

		elif requestCode == self.TEARDOWN:
			self.rtspSeq += 1

			request = 'TEARDOWN ' + self.fileName + ' RTSP/1.0'
			request += '\nCSeq: ' + str(self.rtspSeq)
			request += '\nSession: ' + str(self.sessionId)

			self.rtspSocket.send(request.encode())
			self.requestSent = self.TEARDOWN

		else:
			return

	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		while True:
			reply = self.rtspSocket.recv(256)

			if reply:
				self.parseRtspReply(reply.decode())

			if self.requestSent == self.TEARDOWN:
				self.rtspSocket.shutdown(socket.SHUT_RDWR)
				self.rtspSocket.close()
				break

	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		# The format of the reply:
		# RTSP/1.0 200 OK
		# CSeq: 1
		# Session: 123456

		# print(data)

		request = data.split('\n')
		line1 = request[0].split(' ')
		line2 = request[1].split(' ')

		OK = line1[-1]
		seq = int(line2[-1])

		if seq == self.rtspSeq:
			line3 = request[2].split(' ')
			session = int(line3[-1])

			if self.sessionId == 0:
				self.sessionId = session

			# Process only the sent session
			if self.sessionId == session:
				if OK == 'OK':
					if self.requestSent == self.SETUP and self.state == self.INIT:
						self.state = self.READY
						# Create a datagram socket for receiving RTP data and set timeout
						self.openRtpPort()
					elif self.requestSent == self.PLAY:
						self.state = self.PLAYING
					elif self.requestSent == self.PAUSE:
						self.state = self.READY
						self.playEvent.set()

					elif self.requestSent == self.TEARDOWN:
						self.state = self.INIT
						self.teardownAcked = 1
				else:
					print('Not OK')

	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		# Create a new datagram socket to receive RTP packets from the server
		# self.rtpSocket = ...
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		# Set the timeout value of the socket to 0.5sec
		# ...
		self.rtpSocket.settimeout(0.5)
		try:
			# Bind the RTP sockets for receiving picture frame
			# self.rtpSocket.bind(("", self.rtpPort))
			self.rtpSocket.bind((self.serverAddr, self.rtpPort))
			print("Binded")
		except:
			tkinter.messagebox.showwarning("Fail to bind sockets")

	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		self.pauseMovie()
		# Check if actually quit or mis-clicking
		if tkinter.messagebox.askokcancel("Quit client?", "Click OK to quit"):
			self.exitClient()
		# Resume if mis-click
		else:
			threading.Thread(target=self.listenRtp).start()
			self.sendRtspRequest(self.PLAY)
