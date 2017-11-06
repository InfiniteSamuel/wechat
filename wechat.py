#!/usr/bin/python3
# -*- coding: utf-8 -*-

'''
@author: 'echo'
'''

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import selenium.common.exceptions

import curses
from curses import wrapper
from curses.textpad import rectangle

import pickle
import qrcode
import os.path
import sys, os, traceback

DEBUG = True
LOGINTIMEOUT = 60
PAGELOADTIMEOUT = 15
HEADLESS = True

# recentContacts = {}

def qrTerminalStr(str,version=1):
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

def printIfDebug():
	if DEBUG:
		print("================================================")
		exc_type, exc_value, exc_traceback = sys.exc_info()
		traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
		print("================================================")
 
def getLen(string):
	return int((len(string.decode('utf-8'))+len(string))/2)

def getLoginPage():
	# //img[@mm-src-load="qrcodeLoad"] for the login image
	chrome_options = Options()
	if HEADLESS:
		chrome_options.add_argument("--headless")
	driver = webdriver.Chrome(executable_path=os.path.abspath("chromedriver"), chrome_options=chrome_options)
	if os.path.isfile("cookies.pkl"):
		driver.get("https://wx.qq.com/")
		driver.delete_all_cookies()
		cookies = pickle.load(open("cookies.pkl", "rb"))
		for cookie in cookies:
			driver.add_cookie(cookie)
	#######################################################
	driver.get("https://wx.qq.com/")
	link = driver.find_elements_by_xpath('//img[@mm-src-load="qrcodeLoad"]')
	if len(link) == 0:
		print("No need to sign in. Used session from last time.")
	elif link[0].get_attribute("src").startswith("https://login.weixin.qq.com/qrcode/"):
		qrTerminalStr(link[0].get_attribute("src").replace("qrcode", "l"))
	#######################################################
	try:
		WebDriverWait(driver, timeout=LOGINTIMEOUT).until(
			EC.presence_of_element_located((By.XPATH, '//div[@ng-repeat="chatContact in chatList track by chatContact.UserName"]//span[@class="nickname_text ng-binding"]'))
		)
	except selenium.common.exceptions.TimeoutException:
		print("Login timeout.")
		driver.quit()
		return None
	except:
		printIfDebug()
		return None
	return driver

def getRecentContactList(driver):
	recentContacts = {}
	for link in driver.find_elements_by_xpath('//div[@ng-repeat="chatContact in chatList track by chatContact.UserName"]//span[@class="nickname_text ng-binding"]'):
		if link.text.strip() not in recentContacts:
			recentContacts[link.text.strip()] = len(recentContacts)
		# print("{:3} =>".format(recentContacts[link.text.strip()]), link.text.strip())
	return recentContacts

def chatWith(driver, userName, inputwin, chatwin, maxx, maxx3_1):
	messageNo = 0;
	for link in driver.find_elements_by_xpath('//div[@ng-repeat="chatContact in chatList track by chatContact.UserName"]//span[@class="nickname_text ng-binding"]'):
		if link.text.strip() == userName:
			link.click()
			break;
	for message in driver.find_elements_by_xpath('//pre[@ng-bind-html="message.MMActualContent"]'):
		chatwin.addstr(messageNo, 0, message.text, curses.color_pair(2))
		messageNo += 1
	while True:
		curses.echo()
		inputwin.addstr(0,0, userName+">")
		command = inputwin.getstr(0,getLen((userName+">").encode("utf-8"))+1,maxx-maxx3_1-2).strip()
		inputwin.clear()
		if command.decode("utf-8") == "exit" or command.decode("utf-8") == "quit":
			break;
		elif len(command) > 0:
			editor = driver.find_elements_by_xpath('//pre[@id="editArea"]')[0]
			editor.send_keys(command.decode("utf-8"))
			driver.find_elements_by_xpath('//a[@class="btn btn_send"]')[0].click()

			chatwin.addstr(messageNo, maxx-maxx3_1-2-getLen(command), command, curses.color_pair(1))
			if messageNo == chatwin.getmaxyx()[0]-1:
				chatwin.scroll()
				messageNo -= 1
			chatwin.refresh()
			messageNo += 1
			

def print_help(chatwin):
	chatwin.clear()
	usage = {}
	usage["ls"] 		= "show recent contacts"
	usage["exit"] 		= "exit termial wechat"
	usage["help"] 		= "print this help message"
	usage["open %d"]	= "send message to %d, which is specified by \"ls\""

	lineNo = 2
	chatwin.addstr(0,1, "Following commands are available now:")
	chatwin.addstr(1,1, "=====================================")
	for k in sorted(usage):
		chatwin.addstr(lineNo,1, "{0:15}{1}".format(k, usage[k]))
		lineNo+=1
	chatwin.addstr(lineNo,1, "=====================================")
	chatwin.refresh()

def mainWindow(stdscr, driver):
	curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
	curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)

	maxy = int(stdscr.getmaxyx()[0]-1)
	maxx = int(stdscr.getmaxyx()[1]-2)
	maxy3_1 = int(stdscr.getmaxyx()[0]/3)
	maxx3_1 = int(stdscr.getmaxyx()[1]/3)

	# contacts list
	rectangle(stdscr, 0, 0, maxy, maxx3_1)

	# chat window
	# rectangle(stdscr, 0, maxx3_1, maxy3_1*2, maxx)
	# chatwin = curses.newwin(maxy3_1*2-1, maxx-maxx3_1-1, 0+1, maxx3_1+1)
	rectangle(stdscr, 0, maxx3_1, maxy-2, maxx)
	chatwin = curses.newwin(maxy-3, maxx-maxx3_1-2, 0+1, maxx3_1+1)
	chatwin.scrollok(True)

	# input box
	# rectangle(stdscr, maxy3_1*2, maxx3_1,  maxy, maxx)
	# inputwin = curses.newwin(maxy-maxy3_1*2-1, maxx-maxx3_1-1, maxy3_1*2+1, maxx3_1+1)
	rectangle(stdscr, maxy-2, maxx3_1,  maxy, maxx)
	inputwin = curses.newwin(1, maxx-maxx3_1-1, maxy-1, maxx3_1+1)

	stdscr.refresh()

	chatLines = 0;
	while True:
		recentContacts = getRecentContactList(driver)
		contacts = []
		for i, (k,v) in enumerate(recentContacts.items()):
			rectangle(stdscr, 2*i, 0, 2*(i+1), maxx3_1)
			contacts.append(curses.newwin(1, maxx3_1-2, 2*i+1, 1))
			stdscr.refresh()
			contacts[len(contacts)-1].addstr(0,0, "{:3} => {}".format(v, k))
			contacts[len(contacts)-1].refresh()
		
		curses.echo()
		inputwin.addstr(0,0, ">")
		command = inputwin.getstr(0,2,maxx-maxx3_1-2).strip()
		inputwin.clear()
		if command.decode('utf-8') == "exit" or command.decode('utf-8') == "quit":
			break;
		elif command.decode('utf-8') == "help" or command.decode('utf-8') == "?":
			print_help(chatwin)
		elif command.decode('utf-8').startswith("open "):
			for key, value in recentContacts.items():
				if value == int(command[len("open "):]):
					chatWith(driver, key, inputwin, chatwin, maxx, maxx3_1)
		elif command.decode('utf-8').startswith("cd "):
			for key, value in recentContacts.items():
				if value == int(command[len("cd "):]):
					chatWith(driver, key, inputwin, chatwin, maxx, maxx3_1)

def main():
	driver = None
	try:
		driver = getLoginPage()
		if driver:
			pickle.dump(driver.get_cookies() , open("cookies.pkl","wb"))
			print("Welcome to simple WeChat. Show all the commands please enter \"help\".")
		
		if driver:
			try:
				wrapper(mainWindow, driver)
				# command = input("> ")
				# if command == "exit" or command == "quit":
				# 	break;
				# if command == "help" or command == "?":
				# 	print_help()
				# if command == "ls" or command == "ll":
				# 	getRecentContactList(driver)
				# if command.startswith("open "):
				# 	if len(recentContacts) == 0 or int(command[len("open "):]) >= len(recentContacts):
				# 		print("please use \"ls\" first.")
				# 	else:
				# 		for key, value in recentContacts.items():
				# 			if value == int(command[len("open "):]):
				# 				chatWith(driver, key)
				# if command.startswith("cd "):
				# 	if len(recentContacts) == 0 or int(command[len("cd "):]) >= len(recentContacts):
				# 		print("please use \"ls\" first.")
				# 	else:
				# 		for key, value in recentContacts.items():
				# 			if value == int(command[len("cd "):]):
				# 				chatWith(driver, key)
			except:
				printIfDebug()
		driver.quit()
	except Exception:
		printIfDebug()
	finally:
		if driver != None:
			driver.quit()
			print("Session destroyed.")


if __name__ == "__main__":
	main()