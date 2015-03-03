import json
import MySQLdb
import httplib2
import csv
import base64
from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run
import re

def seed ():
	db = MySQLdb.connect(host='127.0.0.1',db='jcbraunDB',user='root',passwd='3312crystal')
	cursor = db.cursor()
	
	#insert sites from seed and safeSeed csv files
	with open('seed.csv', 'rb') as csvfile:
		seedReader = csv.reader(csvfile, delimiter=',')
		for link in seedReader:
			domain = (link.split("/"))[2]
			execString = ("INSERT IGNORE INTO seed(Domain, URL, URLSource, Crawled) VALUES ('%s', '%s', '%s', '%s');" %(domain, link, 'list', '0')) 
			cursor.execute(execString)
			db.commit()
	with open('safeSeed.csv', 'rb') as csvfile: 
		seedReader = csv.reader(csvfile, delimiter=',')
		for link in seedReader:
			domain = (link.split("/"))[2]
			execString = ("INSERT IGNORE INTO safeSeed(Domain, URL, URLSource, Crawled) VALUES ('%s', '%s', '%s', '%s');" %(domain, link, 'list', '0')) 
			cursor.execute(execString)
			db.commit()	
		
	#get the whitelist from the sql server
	execString = ("SELECT Domain FROM WhiteList;") 
	cursor.execute(execString)
	wl = list(cursor)
	
	#use a file user.json in this directory to log into Gmail and pull down spam
	CLIENT_SECRET_FILE = 'user.json'
	OAUTH_SCOPE = 'https://www.googleapis.com/auth/gmail.readonly'
	STORAGE = Storage('gmail.storage')
	flow = flow_from_clientsecrets(CLIENT_SECRET_FILE, scope=OAUTH_SCOPE)
	http = httplib2.Http()
	credentials = STORAGE.get()
	if credentials is None or credentials.invalid:
	  credentials = run(flow, STORAGE, http=http)
	http = credentials.authorize(http)
	gmail_service = build('gmail', 'v1', http=http)
	spamMsgs = gmail_service.users().messages().list(userId='me', labelIds='SPAM').execute()
	execString = "" 
	i=0
	
	for spam in spamMsgs['messages']:
		i = i+1
		try:
			print spam
			messageId =(spam['id'])
			message = gmail_service.users().messages().get(id=messageId, userId='me').execute()
			stringe = (message['payload']['body'])	
			for part in message['payload']['parts']:
				content = part['body']['data']
				content = base64.urlsafe_b64decode(content.encode('ascii'))
				for url in re.findall('''http["'](.[^"']+)["']''', content):
					try:
						domainTo = (url.split("/"))[2]
						if ((domain + "/") in wl):
							print ("Whitelisted \n")
							bad = 0
						else:
							bad =1
						execString = ("INSERT IGNORE INTO seed (Domain, URL, URLSource, crawled) VALUES ('%s', '%s', 'list', 0);" % (domain, url))
						cursor.execute(execString)
					except:
						print "failed"
				content=db.escape_string(content)
				execString = ("INSERT INTO Content (Lvl, Content, Domain, URL, CopySource) VALUES ('0', '%s', '%i', '%s', 'email');" % (content, i, str(messageId))) 
				cursor.execute(execString)
				db.commit()
		except Exception as e:
			print ("Failed to load email: %s" %execString)	
			print (type(e))
			print (e.args)
	db.close()

