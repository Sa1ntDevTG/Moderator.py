# -*- coding: utf-8 -*-

import aiogram
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.utils.helper import Helper, HelperMode, ListItem
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.callback_data import CallbackData

from models import db_session
from models.users import User
from captcha.image import ImageCaptcha
import psutil
import random
import time

import sys
sys.path.append("./censure")

from censure import Censor

censor_ru = Censor.get(lang='ru')
censor_en = Censor.get(lang='en')

db_session.global_init('database.db')

bot_token = '1827629160:AAGUSA1jhTVFh8w8a1ELlHgLvfn4bVfhNTM'

bot = Bot(token=bot_token)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

cb = CallbackData("id", "text")

class States(Helper):
    mode = HelperMode.snake_case

    CAPTCHA = ListItem()

async def cens(message, text):
	text1 = censor_ru.clean_line(text)
		
	if text != text1[0]:
		if message.from_user.username != None:
			return f'🤐 @{message.from_user.username}\n{text1[0]}'
		else:
			return f'🤐 {message.from_user.first_name}\n{text1[0]}'

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
	global captcha_texts
	#
	iduser = message.from_user.id
	session = db_session.create_session()
	#
	user_all = session.query(User).all()
	T = True
	for all in user_all:
		if all.id == iduser:
			T = False

	if T == True:
		if message.from_user.username:
			session = db_session.create_session()
			name = message.from_user.first_name
			url = message.from_user.username
			iduser = message.from_user.id
			user = User(
				id=iduser,
				name=name,
				username='@'+url,
				carma=0,

				bot='',
				words='',
				bad_words=''
			)
			session.add(user)
			session.commit()
		else:
			session = db_session.create_session()
			name = message.from_user.first_name
			url = message.from_user.username
			iduser = message.from_user.id
			user = User(
				id=iduser,
				name=name,
				username='@...',
				carma=0,

				bot='',
				words='',
				bad_words=''
			)
			session.add(user)
			session.commit()

	if message.chat.id != message.from_user.id:
		await bot.send_message(message.chat.id, '😉 Работаю во всю')
		#pass
	else:
		session = db_session.create_session()
		user_all = session.query(User).all()
		T = False
		for user in user_all:
			if user.id == message.from_user.id:
				T = user.bot
		await bot.send_message(message.chat.id, '🐱 Мяу, Привет! Я бот для чата.\n\nБот удаляет нецензурные слова из вашего чата, а также имеет команды мута, бана и репорта.\n\nУстановить бота очень просто:\n1. Добавить бота в группу\n2. Сделать бота админом группы\n\nПожалуйста, ознакомьтесь с <a href="https://telegra.ph/Politika-konfidencialnosti--CatBot-07-28">политикой конфиденциальности</a> и <a href="https://telegra.ph/Instrukciya--CatBot-07-28">инструкцией</a>.\n\nБот не просит денег и не спамит. Бот просто выполняет свою работу.\nЕсли у вас остались вопросы, напишите разработчику: @vsecoder', parse_mode="HTML")

@dp.message_handler(commands="ping", commands_prefix="!")
async def cmd_ping_bot(message: types.Message):
	user = await bot.get_chat_member(message.chat.id, message.from_user.id)
	if 'administrator' == str(user.status) or 'creator' == str(user.status):

		ram = psutil.virtual_memory()

		reply = "Pong!\n\n"
		reply += " CPU: " + str(psutil.cpu_count()) + " cores (" + str(psutil.cpu_freq().max) + "MHz) with " + str(psutil.cpu_percent()) + "% current usage\n"
		reply += " RAM: " + str(ram.used >> 20) +"mb / "+ str(ram.total >> 20) + "mb\n"

		await message.reply(reply)
	elif message.chat.id == message.from_user.id:

		ram = psutil.virtual_memory()

		reply = "Pong!\n\n"
		reply += " CPU: " + str(psutil.cpu_count()) + " cores (" + str(psutil.cpu_freq().max) + "MHz) with " + str(psutil.cpu_percent()) + "% current usage\n"
		reply += " RAM: " + str(ram.used >> 20) +"mb / "+ str(ram.total >> 20) + "mb\n"

		await message.reply(reply)

@dp.message_handler(commands="stat", commands_prefix="!")
async def cmd_ping_bot(message: types.Message):
	u_id = message.text.replace('!stat ', '')
	info = await bot.get_chat_member(message.chat.id, message.from_user.id)
	if 'administrator' == str(info.status) or 'creator' == str(info.status):
		if message.reply_to_message.from_user.id != None:
			session = db_session.create_session()
			user_all = session.query(User).all()
			bad_words = 0
			words = 0
			for user in user_all:
				if str(user.id) == str(message.reply_to_message.from_user.id):
					bad_words = user.bad_words
					words = user.words
			reply = f'Статистика: {bad_words} плохих слов / {words} всего слов'
			await bot.send_message(message.chat.id, reply,
                                reply_to_message_id=message.message_id)
	elif message.chat.id == message.from_user.id:
		session = db_session.create_session()
		user_all = session.query(User).all()
		bad_words = 0
		words = 0
		for user in user_all:
			if str(user.id) == u_id:
				bad_words = user.bad_words
				words = user.words
		reply = f'Статистика: {bad_words} плохих слов / {words} всего слов'

		await message.reply(reply)

@dp.message_handler(commands=['mute'])
async def mute(message: types.Message):
	try:
		info = await bot.get_chat_member(message.chat.id, message.from_user.id)
		if 'administrator' == str(info.status) or 'creator' == str(info.status):
			if message.reply_to_message.from_user.id != None:
				await bot.restrict_chat_member(
					message.chat.id, message.reply_to_message.from_user.id, until_date=time.time()+600)
				await bot.send_message(message.chat.id, '🤐 Мут на 10 минут осуществлён!',
    	                            reply_to_message_id=message.message_id)
		else:
			pass
	except:
		await bot.send_message(message.chat.id, '🤕 Не получилось')

@dp.message_handler(commands=['unmute'])
async def mute(message: types.Message):
	try:
		info = await bot.get_chat_member(message.chat.id, message.from_user.id)
		if 'administrator' == str(info.status) or 'creator' == str(info.status):
			if message.reply_to_message.from_user.id != None:
				await bot.restrict_chat_member(
					message.chat.id, message.reply_to_message.from_user.id, until_date=time.time())
				await bot.send_message(message.chat.id, '🤐 Мут снят!',
    	                            reply_to_message_id=message.message_id)
		else:
			pass
	except:
		await bot.send_message(message.chat.id, '🤕 Не получилось')

@dp.message_handler(commands=['ban'])
async def mute(message: types.Message):
	try:
		info = await bot.get_chat_member(message.chat.id, message.from_user.id)
		if 'administrator' == str(info.status) or 'creator' == str(info.status):
			if message.reply_to_message.from_user.id != None:
				await bot.kick_chat_member(chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id)
				await bot.send_message(message.chat.id, '🤐 Забанен!')
		else:
			pass
	except Exception as e:
		await bot.send_message(message.chat.id, '🤕 Не получилось')

@dp.message_handler(commands=['unban'])
async def mute(message: types.Message):
	try:
		info = await bot.get_chat_member(message.chat.id, message.from_user.id)
		if 'administrator' == str(info.status) or 'creator' == str(info.status):
			if message.reply_to_message.from_user.id != None:
				await bot.unban_chat_member(chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id)
				await bot.send_message(message.chat.id, '👍 Бан убран!',
    	                            reply_to_message_id=message.message_id)
		else:
			pass
	except:
		await bot.send_message(message.chat.id, '🤕 Не получилось')

@dp.message_handler(commands=['r', 'report'])
async def report(message: types.Message):
	try:
		if message.text == '/report' or message.text == '/r' or not message.reply_to_message:
			await bot.send_message(message.chat.id, '📖Введите причину репорта отвечая на сообщение с нарушением в формате /report spam|flud|18+ или другое')
		else:
			members = await message.chat.get_member(message.reply_to_message.from_user.id)
			info = await bot.get_chat_member(message.chat.id, message.from_user.id)
			report = message.text.replace('/r ', '')
			report = report.replace('/report ', '')
			admins = await bot.get_chat_administrators('@' + message.chat.username)
			send = 0
			for admin in admins:
				if admin.user.username != 'Group_Moder_bot':
					try:
						await bot.send_message(admin.user.id, f'📬 Репорт по причине: ' + str(report) + f'\n\nhttps://t.me/{message.chat.username}/{message.reply_to_message.message_id}')
					except:
						pass
					send += 1

			if send == 0:
				await bot.send_message(message.chat.id, '👮Админы не оповещены, для отправки им репортов надо чтобы они запустили меня в лс!')
			else:
				await bot.send_message(message.chat.id, '👮Админы оповещены')
	except:
		pass

@dp.message_handler(commands=['rules'])
async def rules(message: types.Message):
	await bot.send_message(
		message.chat.id, 'Правила чата: \n'
		'<b> · </b>Не оскорбляйте других участников, не создавайте конфликтных ситуаций. Давайте формировать комьюнити, а не ругаться.'
		'\n<b> · </b>Не используйте нецензурную лексику — сразу удалится ботом.'
		'\n<b> · </b>Нельзя рекламировать услуги, товары, складчины, давать ссылки на конкурентные ресурсы.'
		'\n<b> · </b>Если вы хотите написать в чат, старайтесь уместить свою мысль в одно сообщение — никто не любит флуд.', parse_mode='html')

@dp.message_handler(content_types=["new_chat_members"])
async def newuser(message: types.Message):
	try:
		if message.new_chat_members[0].username == 'Group_Moder_bot':
			await message.reply('😳 О, я в чате! Всем привет, я новый модер этого чата!')
		else:
			await message.send_message(message.chat.id,
				f'🙋Приветствую вас в чате @{message.from_user.username}')#, просим пройти вас тест для подтверждения человечности:\n\n<a href="https://t.me/Group_Moder_bot?start=CAPTCHA">Click</a>', parse_mode='html')
	except BaseException as e:
		name = message.from_user.first_name.replace('<', '')
		name = name.replace('>', '')
		session = db_session.create_session()
		user_all = session.query(User).all()
		T = False
		for user in user_all:
			if user.id == message.from_user.id:
				T = user.bot
		await bot.send_message(
			message.chat.id, f'🙋Приветствую вас в чате <a href="tg://user?id={message.from_user.id}">{name}</a>', parse_mode='html')#, просим пройти вас тест для подтверждения человечности:\n\n<a href="https://t.me/Group_Moder_bot?start=CAPTCHA">Click</a>', parse_mode='html')

@dp.message_handler(content_types=['photo'])
async def photo_check(message: types.Message):
	try:
		session = db_session.create_session()
		user_all = session.query(User).all()
		T = False
		for user in user_all:
			if user.id == message.from_user.id:
				T = user.bot

		
		if message.caption != None:
			censor = await cens(message, message.caption)
			if censor:
				session = db_session.create_session()
				user_all = session.query(User).all()
				bad_words = 0
				for word in censor.split():
					try:
						if word[0:2] == '▓▓':
							bad_words += 1
					except:
						pass
				for user in user_all:
					if user.id == message.from_user.id:
						if user.bad_words != None and user.words != None:
							user.bad_words += bad_words
							user.words += len(message.text.split())
						else:
							user.bad_words = 0
							user.words = 0
				session.commit()
				photoid = message.photo[-1].file_id
				await bot.send_photo(message.chat.id, photoid, caption=str(censor))
				await bot.delete_message(message.chat.id, message.message_id)
			else:
				session = db_session.create_session()
				user_all = session.query(User).all()
				bad_words = 0
				for user in user_all:
					if user.id == message.from_user.id:
						if user.bad_words != None and user.words != None:
							user.bad_words += bad_words
							user.words += len(message.text.split())
						else:
							user.bad_words = 0
							user.words = 0
				session.commit()
	except Exception as e:
		await bot.send_message(1218845111, 'В системе ошибка...\n<code>' + str(e) + '</code>', parse_mode='html')
		await bot.send_message(message.chat.id, 'Упс, ошибка...')

@dp.callback_query_handler(cb.filter())
async def callbacks(call: types.CallbackQuery, callback_data: dict):
    await call.answer(text=callback_data["text"], show_alert=True)

@dp.message_handler(content_types=["text"])
async def check(message: types.Message):
	session = db_session.create_session()
	user_all = session.query(User).all()
	T = False
	for user in user_all:
		if user.id == message.from_user.id:
			T = user.bot
	#if T == 'False':
	#	return await bot.delete_message(message.chat.id, message.message_id)
	try:
		censor = await cens(message, message.text)

		if censor:
			session = db_session.create_session()
			user_all = session.query(User).all()
			bad_words = 0
			for word in censor.split():
				try:
					if word[0:2] == '▓▓':
						bad_words += 1
				except:
					pass
			for user in user_all:
				if user.id == message.from_user.id:
					if user.bad_words != None and user.words != None:
						user.bad_words += bad_words
						user.words += len(message.text.split())
					else:
						user.bad_words = 0
						user.words = 0
			session.commit()
			try:
				keyboard = types.InlineKeyboardMarkup()
				keyboard.add(
					types.InlineKeyboardButton(text="Оригинал", callback_data=cb.new(text=message.text))
				)
				await bot.send_message(message.chat.id, str(censor), reply_markup=keyboard)
				await bot.delete_message(message.chat.id, message.message_id)
			except:
				await bot.send_message(message.chat.id, str(censor))
				await bot.delete_message(message.chat.id, message.message_id)
		else:
			session = db_session.create_session()
			user_all = session.query(User).all()
			bad_words = 0
			for user in user_all:
				if user.id == message.from_user.id:
					if user.bad_words != None and user.words != None:
						user.bad_words += bad_words
						user.words += len(message.text.split())
					else:
						user.bad_words = 0
						user.words = 0
			session.commit()

		iduser = message.from_user.id
		session = db_session.create_session()
		#
		user_all = session.query(User).all()
		T = True
		for all in user_all:
			if all.id == iduser:
				T = False

		if T == True:
			if message.from_user.username:
				session = db_session.create_session()
				name = message.from_user.first_name
				url = message.from_user.username
				iduser = message.from_user.id
				user = User(
                    id=iduser,
                    name=name,
                    username='@'+url,
                    carma=0,

				bot='',
				words='',
				bad_words=''
                )
				session.add(user)
				session.commit()
			else:
				session = db_session.create_session()
				name = message.from_user.first_name
				url = message.from_user.username
				iduser = message.from_user.id
				user = User(
                    id=iduser,
                    name=name,
                    username='@...',
                    carma=0,

				bot='',
				words='',
				bad_words=''
                )
				session.add(user)
				session.commit()
	except BaseException as e:
		await bot.send_message(1218845111, 'В системе ошибка...\n<code>' + str(e) + '</code>', parse_mode='html')
		await bot.send_message(message.chat.id, 'Упс, ошибка...')

@dp.message_handler(content_types=['document'])
async def file_handler(message: types.Message):
	global filescan, allwords, matwords, lastword
	try:
		if message.caption != None:
			censor = await cens(message, message.caption)
			if censor:
				session = db_session.create_session()
				user_all = session.query(User).all()
				bad_words = 0
				for word in censor.split():
					try:
						if word[0:2] == '▓▓':
							bad_words += 1
					except:
						pass
				for user in user_all:
					if user.id == message.from_user.id:
						if user.bad_words != None and user.words != None:
							user.bad_words += bad_words
							user.words += len(message.text.split())
						else:
							user.bad_words = 0
							user.words = 0
				session.commit()
				photoid = message.document.file_id
				await bot.send_document(message.chat.id, photoid, caption=str(censor))
				await bot.delete_message(message.chat.id, message.message_id)
			else:
				session = db_session.create_session()
				user_all = session.query(User).all()
				bad_words = 0
				for user in user_all:
					if user.id == message.from_user.id:
						if user.bad_words != None and user.words != None:
							user.bad_words += bad_words
							user.words += len(message.text.split())
						else:
							user.bad_words = 0
							user.words = 0
				session.commit()
			
		#url_file_scan = 'https://www.virustotal.com/vtapi/v2/file/scan'
		#params = dict(
		#	apikey='<token>')
		#file_upload_id = await bot.get_file(message.document.file_id)
		#url_upload_file = "https://api.telegram.org/file/bot{}/{}".format(
		#	bot_token, file_upload_id.file_path)
		#recvfile = requests.get(url_upload_file)
		#files = dict(file=(recvfile.content))
		#response_file_scan = requests.post(url_file_scan, files=files, params=params)
		#if response_file_scan.json()['response_code'] == 1:
		#	await bot.send_message(message.chat.id, "📎 <a href='" + response_file_scan.json()['permalink'] + "'>Информация</a> о отправленом файле", parse_mode='html')
		#else:
		#	await bot.send_message(message.chat.id, response_file_scan.json()['verbose_msg'])
		#filescan += 1
	except BaseException as e:
		await bot.send_message(1218845111, 'В системе ошибка...\n<code>' + str(e) + '</code>', parse_mode='html')
		#await bot.send_message(message.chat.id, '🧩Файл слишком большой, не получается проверить на вирусы')

@dp.message_handler(state=States.CAPTCHA)
async def captcha_func(message: types.Message):
	result = False
	for captcha in captcha_texts:
		if message.text == captcha:
			result = True
	if result:
		session = db_session.create_session()
		user_all = session.query(User).all()
		T = False
		for user in user_all:
			if user.id == message.from_user.id:
				user.bot = True

		await bot.send_message(message.chat.id, 'Отлично, вы удачно прошли капчу!')

		state = dp.current_state(user=message.from_user.id)
		await state.reset_state()
	else:
		await bot.send_message(message.chat.id, 'Не правильно, попробуйте снова!')


if __name__ == "__main__":
	executor.start_polling(dp)
