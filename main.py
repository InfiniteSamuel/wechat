#!/usr/bin/python3
# -*- coding: utf-8 -*-

'''
@author: 'echo'
'''

import dryscrape # NOTE: This package is not actively maintained. It uses QtWebkit, which is end-of-life and probably doesn't get security fixes backported. Consider using a similar package like Spynner instead.
import webkit_server

import qrcode_terminal

DEBUG = True
def getLoginPage(URL):
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
	session.set_timeout(10)
	session.set_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36")
	try:
		session.visit(URL)
	except Exception as e:
		if DEBUG:
			print(type(e), e.args)
	for link in session.xpath('//img[@mm-src-load="qrcodeLoad"]'):
		qrcode_terminal.draw(link["src"].replace("qrcode", "l"))

	session.wait_for(lambda: session.at_xpath('//div[@ng-repeat="chatContact in chatList track by chatContact.UserName"]//span[@class="nickname_text ng-binding"]'))
	return session

def getRecentContactList(session):
	for link in session.xpath('//div[@ng-repeat="chatContact in chatList track by chatContact.UserName"]//span[@class="nickname_text ng-binding"]'):
		print(link.text())

def main():
	session = getLoginPage("https://wx.qq.com/")
	getRecentContactList(session)

if __name__ == "__main__":
	main()