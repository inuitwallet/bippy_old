import re
import json

def isWif(key, currency):
	with open('currencies.json', 'r') as dataFile:
		currencies = json.load(dataFile)	
	for cur in currencies:
		if cur['currency'] == currency:
			break
	prefixes = cur['prefix'].replace('|', '')
	if re.search("^[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{52}",key):
		return True
	else:
		return False

def isBip(key, currency):
	with open('currencies.json', 'r') as dataFile:
		currencies = json.load(dataFile)	
	for cur in currencies:
		if cur['currency'] == currency:
			break
	if re.search('^' + cur['bipPrefix'] + '[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{56}$', key):
		return True
	else:
		return False
		
def isHex(key):
	if re.search('[0-9A-F]{64}$', key):
		return True
	else:
		return False
		
def isBase64(key):
	if re.search('^[ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789=+\/]{44}$', key):
		return True
	else:
		return False
		
def isBase6(key):
	if re.search('^[012345]{99}$', key):
		return True
	else:
		return False
