#!/opt/bin/python
# coding: utf8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import time
import telepot
from telepot.loop import MessageLoop
import os
import threading
import subprocess

def unpunctuate(str):
	punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
	no_punct = ""
	for char in str:
		if char not in punctuations:
			no_punct = no_punct + char
	return no_punct

def please_wait(chat_id):
	wait_message_id = bot.sendMessage(chat_id, 'Пожалуйста, подождите...').get('message_id', None)
	return (chat_id, wait_message_id,)

def send_error(wait_msg_identifier, stderr, code, fileexist):
	bot.editMessageText(wait_msg_identifier, stderr + "\n" + 'Код ошибки: ' + str(code) + \
		("\n" + 'Файл существует: ' + str(fileexist) if fileexist != None and len(str(fileexist)) > 0 else ''))

def handle_thread(msg, content_type, chat_type, chat_id):
	if chat_id == admin_id:
		if content_type == 'text':
			message = unpunctuate(msg['text'].decode('utf-8').lower()).strip()
			if msg['text'] == '/start':
				bot.sendMessage(chat_id, 'Напишите /help, чтобы узнать, как сканировать')
			elif msg['text'] == '/help' or message == 'справка' or message == 'команды' \
			or message == 'показать справку' or message == 'показать команды' or message == 'показать список команд':
				bot.sendMessage(chat_id, """/help | справка | команды | показать справку | показать команды | показать список команд - эта справка
	/list | сканеры | показать сканеры | список сканеров | показать список сканеров - покажет список сканеров
	/scan [device-name] | сканировать [device-name] - сканирует изображение из устройства device-name""")
			elif msg['text'] == '/list' or message == 'сканеры' or message == 'показать сканеры' \
			or message == 'список сканеров' or message == 'показать список сканеров':
				wait_msg_identifier = please_wait(chat_id)
				devicelist = subprocess.Popen('scanimage -L', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
				devicelist.wait()
				if devicelist.returncode == 0:
					bot.editMessageText(wait_msg_identifier, devicelist.stdout.read())
				else:
					send_error(wait_msg_identifier, devicelist.stderr.read(), devicelist.returncode, None)
			elif msg['text'].startswith('/scan') or message.startswith('сканировать'):
				device = msg['text'].split(None, 1)
				if len(device) == 2:
					device = device[1]
				else:
					device = None
				wait_msg_identifier = please_wait(chat_id)
				if not os.path.isdir(scan_dir):
					os.makedirs(scan_dir)
				filename = time.strftime("%Y-%m-%d_%H-%M-%S.jpg", time.gmtime())
				filepath = os.path.join(scan_dir, filename)
				if(os.path.exists(filepath)):
					os.remove(filepath)
				scanresult = subprocess.Popen('scanimage' + (' -d "' + device + '" ' if device != None else ' ') + \
					'-x 210 -y 297 | convert - jpeg:- > "' + \
					filepath + '"', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
				scanresult.wait()
				fileexist = os.path.exists(filepath)
				if scanresult.returncode == 0 and fileexist:
					file = open(filepath, 'rb')
					bot.sendDocument(chat_id, file)
					bot.deleteMessage(wait_msg_identifier)
					file.close()
					os.remove(filepath)
				else:
					if fileexist:
						os.remove(filepath)
					send_error(wait_msg_identifier, scanresult.stderr.read(), scanresult.returncode, fileexist)
			else:
				bot.sendMessage(chat_id, "Неверная команда, посмотрите справку /help")
		else:
			bot.sendMessage(chat_id, "Неверная команда, посмотрите справку /help")
	else:
		bot.sendMessage(chat_id, "Ошибка: Вы не админ")
def handle(msg):
	content_type, chat_type, chat_id = telepot.glance(msg)

	if chat_type == 'private':
		t = threading.Thread(target=handle_thread, args = (msg, content_type, chat_type, chat_id))
		t.daemon = True
		t.start()

TOKEN = None # Вы должны указать здесь токен от @BotFather
admin_id = None # Вы должны укзать здесь свой ID, узнать его можно у @get_id_bot
scan_dir = '/var/scans'

bot = telepot.Bot(TOKEN)
MessageLoop(bot, handle).run_as_thread()

# Keep the program running.
while 1:
	time.sleep(10)