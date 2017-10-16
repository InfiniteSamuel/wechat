#!/usr/bin/python3
# -*- coding: utf-8 -*-

'''
@author: 'echo'
'''

import dryscrape # NOTE: This package is not actively maintained. It uses QtWebkit, which is end-of-life and probably doesn't get security fixes backported. Consider using a similar package like Spynner instead.
import webkit_server
import qrcode
import os.path

DEBUG = True
LOGINTIMEOUT = 60
PAGELOADTIMEOUT = 15

recentContacts = {}

def qr_terminal_str(str,version=1):
	white_block = '\033[0;37;47m  '
	black_block = '\033[0;37;40m  '
	new_line = '\033[0m\n'
	qr = qrcode.QRCode(version)
	qr.add_data(str)
	qr.make()
	output = white_block*(qr.modules_count+2) + new_line
	for mn in qr.modules:
		output += white_block
		for m in mn:
			if m:
				output += black_block
			else:
				output += white_block
		output += white_block + new_line
	output += white_block*(qr.modules_count+2) + new_line
	print(output)
	return False

def getLoginPage():
	# //img[@mm-src-load="qrcodeLoad"] for the login image
	try:
		session = dryscrape.Session()
	except webkit_server.NoX11Error: 
		dryscrape.start_xvfb()
		session = dryscrape.Session()
	except Exception as e:
		if DEBUG:
			print(e)
	session.set_attribute('auto_load_images', False)
	session.set_timeout(PAGELOADTIMEOUT)
	session.set_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36")
	if os.path.isfile("cookie"):
		with open("cookie", "r") as f:
			for line in f:
				session.set_cookie(line)
	#######################################################
	while True:
		try:
			session.visit("https://wx.qq.com/")
		except webkit_server.InvalidResponseError:
			if DEBUG:
				print("Retrying...")
			continue
		except Exception as e:
			if DEBUG:
				# print(type(e), e.args)
				print(e)
		link = session.at_xpath('//img[@mm-src-load="qrcodeLoad"]')
		if link is None:
			print("No need to sign in. Used session from last time.")
			break
		if link["src"].startswith("https://login.weixin.qq.com/qrcode/"):
			qr_terminal_str(link["src"].replace("qrcode", "l"))
			break
	#######################################################
	try:
		session.wait_for(lambda: session.at_xpath('//div[@ng-repeat="chatContact in chatList track by chatContact.UserName"]//span[@class="nickname_text ng-binding"]'), timeout=LOGINTIMEOUT)
	except dryscrape.mixins.WaitTimeoutError:
		print("Login timeout.")
		return None
	return session

def getRecentContactList(session):
	for link in session.xpath('//div[@ng-repeat="chatContact in chatList track by chatContact.UserName"]//span[@class="nickname_text ng-binding"]'):
		print("{:3} =>".format(len(recentContacts)), link.text())
		recentContacts[len(recentContacts)] = link.text().strip()

def chatWith(session, userName):
	for link in session.xpath('//div[@ng-repeat="chatContact in chatList track by chatContact.UserName"]//span[@class="nickname_text ng-binding"]'):
		if link.text().strip() == userName:
			link.click()
			break;
	for message in session.xpath('//pre[@ng-bind-html="message.MMActualContent"]'):
		print(message.text())
	while True:
		command = input(userName + "> ")
		if command == "exit" or command == "quit":
			break;
		else:
			editor = session.at_xpath('//pre[@id="editArea"]')
			editor.set(command)
			
			print(editor.text())
			session.at_xpath('//a[@class="btn btn_send"]').click()

def print_help():
	usage = {}
	usage["ls"] 		= "show recent contacts"
	usage["exit"] 		= "exit termial wechat"
	usage["help"] 		= "print this help message"
	usage["open %d"]	= "send message to %d, which is specified by \"ls\""

	print("Following commands are available now:")
	print("=====================================")
	for k in sorted(usage):
		print("{0:15}{1}".format(k, usage[k]))
	print("=====================================")

def main():
	session = getLoginPage()
	if session:
		cookies = session.cookies()
		with open("cookie", "w") as f:
			for i in cookies:
				f.write(i+"\n")
		print("Welcome to simple WeChat. Show all the commands please enter \"help\".")
	
	while session:
		command = input("> ")
		if command == "exit" or command == "quit":
			break;
		if command == "help" or command == "?":
			print_help()
		if command == "ls" or command == "ll":
			getRecentContactList(session)
		if command.startswith("open "):
			if len(recentContacts) == 0:
				print("please use \"ls\" first.")
			else:
				chatWith(session, recentContacts[int(command[len("open "):].strip())])
	print("Session destroyed.")

if __name__ == "__main__":
	main()