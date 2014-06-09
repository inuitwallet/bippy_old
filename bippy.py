"""
	bippy.
	Simple tool for enabling BIP 38 encryption of a variety of crypto-currency private keys
	
	Sponsored by http://woodwallets.io
	Written by the creator of inuit (http://inuit-wallet.co.uk)
"""

from kivy.config import Config
Config.set('graphics', 'width', '1000')
Config.set('graphics', 'height', '400')
Config.set('graphics', 'resizable', '0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.label import Label
from kivy.uix.image import AsyncImage
from kivy.uix.progressbar import ProgressBar
from kivy.uix.button import Button
from kivy.graphics import Color, Ellipse
from kivy.clock import Clock

import system.gen as gen
import system.key as key
import json

import encrypt.electrum as electrum

currencyLongNamesList = ['Bitcoin','Litecoin','Dogecoin','Peercoin','Blackcoin','Vertcoin','----------Currencies below are not currently available at woodwallets.io----------']

with open('currencies.json', 'r') as dataFile:
	currencies = json.load(dataFile)	
for cur in currencies:
	if cur['longName'] not in currencyLongNamesList:
		currencyLongNamesList.append(cur['longName'])

class bippyApp(App):
	"""
		Main Application Class required for Kivy
	"""

	def getCur(self, instance, value=False):
		"""
			From the currency longName returned by the UI
			return the Abbreviation understood by the rest of the application
		"""
		if value == '----------Currencies below are not currently available at woodwallets.io----------':
			instance.text = self.selectedCurrencyLongName
			return
		for cur in currencies:
			if cur['longName'] == value:
				self.selectedCurrency = str(cur['currency'])
				self.selectedCurrencyLongName = str(cur['longName'])
				return

	def checkPrivK(self, instance, value=False):
		"""
			Perform various checks on the private key data and act accordingly
			This is called whenever the Private Key entry box looses focus
		"""

		if value:
			return
		testKey = instance.text
		self.PasswordEnter.text = ''
		self.entropyImage.unbind(on_touch_move=self.draw)
		self.prog.value = 0
		self.entropyImage.canvas.remove_group('ellipses')

		#Test if it is an electrum seed
		if key.isElectrumSeed(testKey):
			self.MainLabel.text = 'It looks like you entered an Electrum seed.\n\nEnter a Passphrase to encrypt it.'
			self.PrivKLabel.text = 'Electrum Seed'
			self.PassLabel.text = 'Enter\nPassphrase'
			return

		#Test if it is an encrypted electrum Seed
		if key.isEncElectrumSeed(testKey):
			self.MainLabel.text = 'It looks like you\'ve entered an encrypted Electrum Seed.\n\nEnter your Passphrase to decrypt it.'
			self.PrivKLabel.text = 'Encrypted\nElectrum Seed'
			self.PassLabel.text = 'Enter Passphrase'
			return

		#Test if its a BIP encrypted Key
		if key.isBip(testKey, self.selectedCurrency):
			self.MainLabel.text = 'It looks like you entered a BIP0038 encrypted Private Key.\n\nEnter your Passphrase to decrypt it.'
			self.PrivKLabel.text = 'Encrypted Key'
			self.PassLabel.text = 'Encryption\nPassphrase'
			return

		#Test if it's a Private key
		if key.isWif(testKey, self.selectedCurrency) or key.isHex(testKey) or key.isBase64(testKey) or key.isBase6(testKey):
			self.MainLabel.text = 'You\'ve entered a Private Key.\n\nEnter a Passphrase to encrypt it.'
			self.PrivKLabel.text = 'Private Key'
			self.PassLabel.text = 'Enter\nPassphrase'
			return

		#reset to standard if the box is empty
		if testKey == '':
			self.MainLabel.text = '[b]Welcome to bippy[/b]\n\nTo get started choose a currency and enter an encryption passphrase.\n\nIf you already have a private key you would like to encrypt or decrypt,\n\nenter it in the \'Private Key\' box below'
			self.PrivKLabel.text = 'Private Key\n(optional)'
			self.PassLabel.text = 'Passphrase'
			return

		#otherwise let the user know that they haven't entered a recognised Private Key
		self.MainLabel.text = 'bippy can\'t recognise what you entered as a private key.\n\nAcceptable formats are:\nCompressed WIF, HEX, Base64, Base6, BIP Encrypted'
		self.PrivKLabel.text = 'Private Key\n(optional)'
		self.PassLabel.text = 'Passphrase'
		return

	def checkPassword(self, instance, value=False):
		"""
			This is called whenever the password field looses focus
			perform checks and validation on the password field and initiate encryption/decryption if data is correct
		"""
		if value:
			return

		self.Password = instance.text

		if gen.verifyPassword(self.Password) is False:
			self.MainLabel.text = 'Passphrases must be 7 characters or longer'
			self.entropyImage.unbind(on_touch_move=self.draw)
			self.prog.value = 0
			self.entropyImage.canvas.remove_group('ellipses')
			return
		#need to have some sort of password length and complexity check here

		self.PrivateKey = self.PrivK.text

		#it could be a BIP key in which case we show the Decrypt button
		if key.isBip(self.PrivateKey, self.selectedCurrency):
			self.MainLabel.text = 'Hit the \'Decrypt\' button to start the decryption.'
			self.rightBox.remove_widget(self.prog)
			self.rightBox.add_widget(self.decButton)
			return

		#It could be an Electrum Seed in which case we show the Electrum encrypt button
		if key.isElectrumSeed(self.PrivateKey):
			self.MainLabel.text = 'Hit the \'Encrypt\' button to start the encryption of your Electrum Seed'
			self.rightBox.remove_widget(self.prog)
			self.rightBox.add_widget(self.encElectrumButton)
			return

		#It could be an encrypted Electrum seed in which case weshow the Electrum Decrypt button
		if key.isEncElectrumSeed(self.PrivateKey):
			self.MainLabel.text = 'Hit the \'Decrypt\' button to decrypt your Electrum Seed'
			self.rightBox.remove_widget(self.prog)
			self.rightBox.add_widget(self.decElectrumButton)
			return

		#otherwise check that the entry isn't a WIF, HEX B64 or B6 key
		#if there is no valid privatekey we ask for entropy to be entered
		#This then generates a new key pair
		if not key.isWif(self.PrivateKey, self.selectedCurrency) and not key.isHex(self.PrivateKey) and not key.isBase64(self.PrivateKey) and not key.isBase6(self.PrivateKey):
			self.PrivK.text = ''
			self.PrivateKey = None
			self.MainLabel.text = 'To generate a BIP0038 encrypted key you need to generate some randomness.\n\nHold your left mouse button down and move it about on the image to the right to do this and fill up the bar.'
			self.entropy = []
			self.entropyImage.bind(on_touch_move=self.draw)
			return

		#otherwise there is a user supplied private key so we offer to generate a BIP key
		self.MainLabel.text = 'Hit the \'Encrypt\' button to start the encryption of your private key'
		self.rightBox.remove_widget(self.prog)
		self.rightBox.add_widget(self.encButton)
		return

	def draw(self, instance, value):
		"""
			This function is enabled when only a password has been entered.
			It allows the user to draw on the image shown to the right of the UI
			This is the method by which entropy is gathered for generation of key pairs
		"""
		with self.entropyImage.canvas:
			Color(0, 0.86667, 1)
			d = 5.
			if self.entropyImage.collide_point(value.x, value.y):
				Ellipse(pos=(value.x - d / 2, value.y - d / 2), size=(d, d), group='ellipses')
				self.entropy.append((int(value.x),int(value.y)))
				self.prog.value += 1
		if self.prog.value == 550:
			self.entropyImage.unbind(on_touch_move=self.draw)
			self.prog.value = 0
			self.entropyImage.canvas.remove_group('ellipses')
			#got everything we need. replace the progress bar with a generate button
			self.rightBox.remove_widget(self.prog)
			self.rightBox.add_widget(self.encButton)
			self.MainLabel.text='You have generated enough Randomness.\n\nHit the \'Encrypt\' button to start the encryption.\n\n(bippy may become unresponsive for ~10 seconds while encryption takes place)'
		return

	def generateBIP(self, instance, value=False):
		"""
			Generate the BIP Private Key
		"""
		self.MainLabel.text='Starting BIP0038 Encryption'
		#use clock to delay the start of the encryption otherwise the message above is never shown
		Clock.schedule_once(self.genBIP, 0.5)
		return

	def genBIP(self, dt):
		"""
			This is the second part of the generate BIP method.
			It's split into two like this as otherwise the UI doesn't update to show that encryption has started
		"""
		if self.PrivateKey is None:
			BIP, Address = gen.genBIPKey(self.selectedCurrency, self.Password, self.entropy)
		else:
			BIP, Address = gen.encBIPKey(self.PrivateKey, self.selectedCurrency, self.Password)
		self.setBIP(BIP, Address)
		return

	def decryptBIP(self, instance, value=False):
		"""
			Decrypt the BIP key
		"""
		self.MainLabel.text='Starting BIP0038 Decryption'
		#use clock to delay the start of the encryption otherwise the message above is never shown
		Clock.schedule_once(self.decBIP, 0.5)
		return

	def decBIP(self, dt):
		"""
			Second part of the decryption routine to allow UI to update
		"""
		PrivateKey, PublicAddress = gen.decBIPKey(self.PrivateKey, self.Password, self.selectedCurrency)
		if PrivateKey is False:
			self.MainLabel.text = 'BIP0038 Decryption was unsuccessful.\n\nAre you sure the passphrase was correct?'
			self.rightBox.remove_widget(self.prog)
			self.rightBox.remove_widget(self.decButton)
			self.rightBox.add_widget(self.resetButton)
			return
		self.MainLabel.text = 'BIP0038 Decryption was successful.\n\nSee below for your private key and address.'
		self.PrivKLabel.text = 'Decrypted\nPrivate Key'
		self.PassLabel.text = 'Address'
		self.PasswordEnter.password = False
		self.PrivK.text = PrivateKey
		self.PasswordEnter.text = PublicAddress
		#unbind the private key and password entry boxes so that the user can copy out the key and address
		self.PrivK.unbind(focus=self.checkPrivK)
		self.PasswordEnter.unbind(focus=self.checkPassword)
		self.rightBox.remove_widget(self.prog)
		self.rightBox.remove_widget(self.decButton)
		self.rightBox.add_widget(self.resetButton)
		return

	def setBIP(self, BIP, Address):
		"""
			This method updates the UI with the output of encryption
		"""
		#re-shuffle the visible widgets so that the links become available
		self.leftBox.remove_widget(self.MainLabel)
		self.leftBox.remove_widget(self.entryPane)
		self.leftBox.add_widget(self.LinksTab)
		self.leftBox.add_widget(self.entryPane)
		self.PrivKLabel.text = 'BIP0038 Key'
		self.PassLabel.text = 'Address'
		self.DoubleLink.text = 'https://woodwallets.io/product/woodwallet-private-key-and-public-address?dbl_addr=' + Address + '&dbl_pvtkey=' + BIP + '&dbl_coin=' + self.selectedCurrency + '&orig=bippy'
		self.PrivateLink.text = 'https://woodwallets.io/product/one-side-private-key-only?pvt_pvtkey=' + BIP + '&pvt_coin=' + self.selectedCurrency + '&orig=bippy'
		self.PublicLink.text = 'https://woodwallets.io/product/woodwallet-public-address?pub_addr=' + Address + '&pub_coin=' + self.selectedCurrency + '&orig=bippy'

		self.PasswordEnter.password = False
		self.PrivK.text = BIP
		self.PasswordEnter.text = Address
		#unbind the private key and password enty boxes so that the user can copy out the key and address
		self.PrivK.unbind(focus=self.checkPrivK)
		self.PasswordEnter.unbind(focus=self.checkPassword)
		self.rightBox.remove_widget(self.prog)
		self.rightBox.remove_widget(self.encButton)
		self.rightBox.add_widget(self.resetButton)
		return

	def resetUI(self, instance, value=False):
		"""
			This is called when the reset button is pressed.
			The UI is restored to its initial state
		"""
		self.leftBox.remove_widget(self.LinksTab)
		self.leftBox.remove_widget(self.MainLabel)
		self.leftBox.remove_widget(self.entryPane)
		self.leftBox.add_widget(self.MainLabel)
		self.leftBox.add_widget(self.entryPane)
		self.MainLabel.text='[b]Welcome to bippy[/b]\n\nTo get started choose a currency and enter an encryption passphrase.\n\nIf you already have a private key you would like to encrypt or decrypt,\n\nenter it in the \'Private Key\' box below'
		self.PrivKLabel.text='Private Key\n(optional)'
		self.PrivK.text = ''
		self.PassLabel.text='Passphrase'
		self.PasswordEnter.password = True
		self.PasswordEnter.text = ''
		#rebind the private key and password entry boxes
		self.PrivK.bind(focus=self.checkPrivK)
		self.PasswordEnter.bind(focus=self.checkPassword)
		self.rightBox.remove_widget(self.resetButton)
		self.rightBox.remove_widget(self.encButton)
		self.rightBox.remove_widget(self.decButton)
		self.rightBox.add_widget(self.prog)
		return

	def encryptElectrum(self, instance, value=False):
		"""
			Encrypt the Electrum Seed
		"""
		self.MainLabel.text='Starting Encryption of Electrum Seed'
		#use clock to delay the start of the encryption otherwise the message above is never shown
		self.PrivK.text = ''
		Clock.schedule_once(self.encElectrum, 0.5)
		return

	def encElectrum(self, dt):
		"""
			Begin encryption of the supplied Electrum Seed
		"""
		encryptedSeed = electrum.encrypt(self.PrivateKey, self.Password)
		self.MainLabel.text = 'Encryption was successful.\n\nSee below for your encrypted seed'
		self.PrivKLabel.text = 'Encrypted\nElectrum Seed'
		self.PassLabel.text = ''
		self.PrivK.text = encryptedSeed
		self.PasswordEnter.text = ''
		#unbind the private key and password entry boxes so that the user can copy out the key and address
		self.PrivK.unbind(focus=self.checkPrivK)
		self.PasswordEnter.unbind(focus=self.checkPassword)
		self.rightBox.remove_widget(self.prog)
		self.rightBox.remove_widget(self.encElectrumButton)
		self.rightBox.add_widget(self.resetButton)
		return

	def decryptElectrum(self, instance, value=False):
		"""
			Start the decryption of the Electrum Seed
		"""
		self.MainLabel.text='Starting the Decryption of your Electrum seed'
		#use clock to delay the start of the decryption otherwise the message above is never shown
		self.PrivK.text = ''
		self.PasswordEnter.text = ''
		Clock.schedule_once(self.decElectrum, 0.5)
		return

	def decElectrum(self, dt):
		"""
			Perform the actual decryption of the Electrum Seed
		"""
		decryptedSeed = electrum.decrypt(self.PrivateKey, self.Password)
		if decryptedSeed is False:
			self.MainLabel.text = 'Decryption was not successful.\n\nAre you sure you entered the correct passphrase?\n\nReset to try again'
			self.rightBox.remove_widget(self.prog)
			self.rightBox.remove_widget(self.decElectrumButton)
			self.rightBox.add_widget(self.resetButton)
			return
		self.MainLabel.text = 'Decryption was successful.\n\nSee below for your Electrum Seed.'
		self.PrivKLabel.text = 'Decrypted\nElectrum Seed'
		self.PassLabel.text = ''
		self.PasswordEnter.password = False
		self.PrivK.text = decryptedSeed
		self.PasswordEnter.text = ''
		#unbind the private key and password entry boxes so that the user can copy out the key and address
		self.PrivK.unbind(focus=self.checkPrivK)
		self.PasswordEnter.unbind(focus=self.checkPassword)
		self.rightBox.remove_widget(self.prog)
		self.rightBox.remove_widget(self.decElectrumButton)
		self.rightBox.add_widget(self.resetButton)
		return

	def build(self):
		"""
			Build the UI
		"""

		#root layout is a horizontal box layout
		self.root = BoxLayout(spacing=10, padding=[5,5,5,5])

		#the right box has another BoxLayout.
		self.rightBox = BoxLayout(orientation='vertical', size_hint=(.25, 1))

		#the image goes in the top part
		self.entropyImage = AsyncImage(source='woodFORbippy.png', size_hint=(1, .9), allow_stretch=True, keep_ratio=True)
		self.rightBox.add_widget(self.entropyImage)
		#the progress bar in the bottom
		self.prog = ProgressBar(max=550, size_hint=(.9,.1), pos_hint={'right':.95})
		self.rightBox.add_widget(self.prog)
		#the encrypt button.
		#this isn't added to the UI until Entropy has been collected
		#the first version is for BIP 38 keys. The second is for Electrum Seeds
		self.encButton = Button(text='Encrypt', size_hint=(.9,.1), pos_hint={'right':.95})
		self.encButton.bind(on_press=self.generateBIP)
		self.encElectrumButton = Button(text='Encrypt', size_hint=(.9,.1), pos_hint={'right':.95})
		self.encElectrumButton.bind(on_press=self.encryptElectrum)
		#the decrypt button.
		#this isn't added to the UI until decryption possibilities have been noticed
		self.decButton = Button(text='Decrypt', size_hint=(.9,.1), pos_hint={'right':.95})
		self.decButton.bind(on_press=self.decryptBIP)
		self.decElectrumButton = Button(text='Decrypt', size_hint=(.9,.1), pos_hint={'right':.95})
		self.decElectrumButton.bind(on_press=self.decryptElectrum)
		#the reset button.
		#this isn't added to the UI until Encryption has taken place
		self.resetButton = Button(text='Reset', size_hint=(.9,.1), pos_hint={'right':.95})
		self.resetButton.bind(on_press=self.resetUI)

		#within the left hand box we split into a vertical box layout
		self.leftBox = BoxLayout(orientation='vertical', size_hint=(.7,1))

		#the top of the left hand box is a label
		self.MainLabel = Label(text_size=(720,150), font_size=15, shorten=True, halign='center', valign='middle', markup=True, text='[b]Welcome to bippy[/b]\n\nTo get started choose a currency and enter an encryption passphrase.\n\nIf you already have a private key you would like to encrypt or decrypt,\n\nenter it in the \'Private Key\' box below', size_hint=(1, .4))
		self.leftBox.add_widget(self.MainLabel)

		#for displaying the links we have an accordion layout
		#build it here even though it is only attached after encryption has taken place
		self.LinksTab = Accordion(size_hint=(1, .4))
		self.Links = AccordionItem(title='Links', )
		self.LinksGrid = GridLayout(cols=2, padding=(10, 10, 10, 10), spacing=(10, 20))
		self.LinksGrid.add_widget(Label(text='Double Sided', font_size=11, size_hint=(.3,1), text_size=(100,50), halign='center', valign='middle'))
		self.DoubleLink = TextInput(multiline=False, size_hint_y=None, height=30)
		self.LinksGrid.add_widget(self.DoubleLink)
		self.LinksGrid.add_widget(Label(text='Single Sided Private Key', font_size=11, size_hint=(.3,1), text_size=(100,50), halign='center', valign='middle'))
		self.PrivateLink = TextInput(multiline=False, size_hint_y=None, height=30)
		self.LinksGrid.add_widget(self.PrivateLink)
		self.LinksGrid.add_widget(Label(text='Single Sided Public Address', font_size=11, size_hint=(.3,1), text_size=(100,50), halign='center', valign='middle'))
		self.PublicLink = TextInput(multiline=False, size_hint_y=None, height=30)
		self.LinksGrid.add_widget(self.PublicLink)
		self.Links.add_widget(self.LinksGrid)
		self.Message = AccordionItem(title='Complete', )
		self.MessageLabel = Label(halign='center', valign='middle', text='BIP0038 encryption is complete\n\nSee below for your encrypted private key and address\n\nSee the \'Links\' tab to the left for direct links to purchase Wood Wallets')
		self.Message.add_widget(self.MessageLabel)
		#add the two 'tabs' to the main accordion widget
		self.LinksTab.add_widget(self.Links)
		self.LinksTab.add_widget(self.Message)

		#the bottom of the left hand pane is a grid layout
		self.entryPane = GridLayout(cols=2, size_hint=(1, .6), padding=(10, 40, 10, 40), spacing=(10, 40))
		#within this pane we have the Text Input boxes and labels
		#Currency
		self.entryPane.add_widget(Label(text='Currency', size_hint_x=None, width=100))
		self.Currency = Spinner(text='Bitcoin', values=currencyLongNamesList, size_hint_x=None, size_hint_y=None, height=40, width=50)
		self.Currency.bind(text=self.getCur)
		self.selectedCurrency = 'BTC'
		self.selectedCurrencyLongName = 'Bitcoin'
		self.entryPane.add_widget(self.Currency)
		#Private Key
		self.PrivKLabel = Label(text='Private Key\n(optional)', size_hint_x=None, width=100)
		self.entryPane.add_widget(self.PrivKLabel)
		self.PrivK = TextInput(size_hint_y=None, height=30, multiline=False)
		self.PrivK.bind(focus=self.checkPrivK)
		self.entryPane.add_widget(self.PrivK)
		#Password
		self.PassLabel = Label(text='Passphrase', size_hint_x=None, width=100)
		self.entryPane.add_widget(self.PassLabel)
		self.PasswordEnter = TextInput(size_hint_y=None, height=30, multiline=False, password=True)
		self.PasswordEnter.bind(focus=self.checkPassword)
		self.entryPane.add_widget(self.PasswordEnter)

		#add the entry pane to the left box
		self.leftBox.add_widget(self.entryPane)
		#add the left box to the root widget
		self.root.add_widget(self.leftBox)
		#add the rightbox to the root widget
		self.root.add_widget(self.rightBox)

		print(electrum.buildRandom())
		return self.root

if __name__ == '__main__':
	bippyApp().run()