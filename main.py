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
import pickle
import qrcode
import os.path
import sys, os, traceback

DEBUG = True
LOGINTIMEOUT = 60
PAGELOADTIMEOUT = 15
HEADLESS = True

recentContacts = {}

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
		traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
		print("================================================")

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
	for link in driver.find_elements_by_xpath('//div[@ng-repeat="chatContact in chatList track by chatContact.UserName"]//span[@class="nickname_text ng-binding"]'):
		if link.text.strip() not in recentContacts:
			recentContacts[link.text.strip()] = len(recentContacts)
		print("{:3} =>".format(recentContacts[link.text.strip()]), link.text.strip())

def chatWith(driver, userName):
	for link in driver.find_elements_by_xpath('//div[@ng-repeat="chatContact in chatList track by chatContact.UserName"]//span[@class="nickname_text ng-binding"]'):
		if link.text.strip() == userName:
			link.click()
			break;
	for message in driver.find_elements_by_xpath('//pre[@ng-bind-html="message.MMActualContent"]'):
		print(message.text)
	while True:
		command = input(userName + "> ")
		if command == "exit" or command == "quit":
			break;
		else:
			editor = driver.find_elements_by_xpath('//pre[@id="editArea"]')[0]
			editor.send_keys(command)
			
			driver.find_elements_by_xpath('//a[@class="btn btn_send"]')[0].click()

			

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
	driver = None
	try:
		driver = getLoginPage()
		if driver:
			pickle.dump(driver.get_cookies() , open("cookies.pkl","wb"))
			# with open("cookie", "w") as f:
			# 	for cookie in driver.get_cookies():
			# 		f.write(cookie['name'] + ":->" + cookie['value']+"\n")
			print("Welcome to simple WeChat. Show all the commands please enter \"help\".")
		
		while driver:
			try:
				command = input("> ")
				if command == "exit" or command == "quit":
					break;
				if command == "help" or command == "?":
					print_help()
				if command == "ls" or command == "ll":
					getRecentContactList(driver)
				if command.startswith("open "):
					if len(recentContacts) == 0 or int(command[len("open "):]) >= len(recentContacts):
						print("please use \"ls\" first.")
					else:
						for key, value in recentContacts.items():
							if value == int(command[len("open "):]):
								chatWith(driver, key)
				if command.startswith("cd "):
					if len(recentContacts) == 0 or int(command[len("cd "):]) >= len(recentContacts):
						print("please use \"ls\" first.")
					else:
						for key, value in recentContacts.items():
							if value == int(command[len("cd "):]):
								chatWith(driver, key)
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