import sys
from tkinter import Tk
from Client import Client
from Client_3_buttons import Client_3_buttons
from Client_describe import Client_describe
from Client_with_config import Client_with_config

if __name__ == "__main__":
	try:
		serverAddr = sys.argv[1]
		serverPort = sys.argv[2]
		rtpPort = sys.argv[3]
		fileName = sys.argv[4]
	except:
		print("[Usage: ClientLauncher.py Server_name Server_port RTP_port Video_file]\n")

	root = Tk()

	# Create a new client

	app = Client(root, serverAddr, serverPort, rtpPort, fileName)
	# app = Client_3_buttons(root, serverAddr, serverPort, rtpPort, fileName)
	# app = Client_describe(root, serverAddr, serverPort, rtpPort, fileName)
	# app = Client_with_config(root, serverAddr, serverPort, rtpPort, fileName)
	app.master.title("RTPClient")	
	root.mainloop()
	