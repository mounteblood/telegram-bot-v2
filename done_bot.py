
import io
import chardet
import os
from random import randint, randrange
import codecs
import pprint
import emojis
import telebot
from telebot.types import MessageEntity, Message
pp = pprint.PrettyPrinter(indent=4)
from telethon import TelegramClient, sync
import configparser
import multiprocessing
from multiprocessing import Value, Array
import datetime
import random
import pickle

WANNA_ACTIVATE_PHONES_BEFORE_USING = False

def log_a_note(string):
  print(string)
  with open("log.txt", 'at') as logger:
    curr_time = datetime.datetime.now()
    logger.write(str(curr_time) + " | " + string + "\r")

log_a_note("SCRIPT IS LOADING")

config = configparser.ConfigParser()
config.read("mysettings.ini")
bot_token = config["Posts"]["bot_token"]
api_id = config["Posts"]["api_id1"]
no_post = True
maximum = 50
limit = Value('i', 10)
stop = Value('i', 1)
recheck = Value('i', 0)
interval_low = Value('i', 1 * 60  + 30)
interval_high = Value('i', 2 * 60  + 30)
posts = Array('i', [0 for x in range(maximum)])

log_a_note("INIT PASSED")

texts = []
recheck.value = 1

def get_post_text(id_):
  global texts
  texts = []
  for x in range(maximum):
    try:
      with open(f"text{x}.pkl", 'rb') as f:
        data = pickle.load(f)
        texts.append(data)
    except Exception as e:
      texts.append("No Text Available")
  return texts[id_]
  return data

def sender(limit, stop, interval_low, interval_high, posts):
  import time
  global config
  global log_a_note
  index_max = 10
  accounts = []
  t = 0
  dialog_list = []
  d_accs = {}
  dialogs = []
  counter = 0
  api_id = config["Posts"]["api_id1"]
  while True:
    t += 1
    try:
      api_id = config["Posts"][f"api_id{t}"]
      api_hash = config['Posts'][f"api_hash{t}"]
      phone = config['Posts'][f'phone{t}']
      client = TelegramClient(f'session_name_#{t}', api_id, api_hash)
      client.connect()
      counter += 1
      if not client.is_user_authorized():
        client.send_code_request(phone)
        a = input(f"Phone => {phone}, Enter TG Code:")
        client.sign_in(phone, a)
        log_a_note(f"PHONE {phone} AUTH SUCCESSFUL")
      sub_dialogs = client.get_dialogs()
      accounts.append(client)
      for dialog in sub_dialogs:
        dialogs.append([client, dialog])
        if dialog.id < 0:
          dialog_list.append(dialog.id)
      log_a_note(f"PHONE \" {phone} \" IS LOADED SUCCESSFUL")
    except Exception as e:
      break
  if WANNA_ACTIVATE_PHONES_BEFORE_USING:
    print(f"{counter} Accounts is Ready!")
    exit()
  for x in dialog_list:
    for client, dialog in dialogs:
      if dialog.id == x:
        try:
          l = d_accs[dialog.id]
        except Exception as e:
          d_accs[dialog.id] = []
        d_accs[dialog.id].append(client)
  dialog_list = set(dialog_list)
  log_a_note(f"{counter} PHONES IS ACTIVE")
  index = 0
  curr_time = datetime.datetime.now()
  with open("log.txt", 'at') as logger:
    while True:
      time.sleep(0.01)
      for x in range(len(posts)):
        if x >= limit.value:
          continue
        for _ , dialog_id in dialog_list:
          if dialog_id < 0:
            try:
              client = random.choice(d_accs[dialog_id])
              while stop.value == 0:
                time.sleep(0.1)
              if posts[x] == 0:
                if get_post_text(x) != 'No Text Available':
                  if no_post:
                    try:
                      with open(f"pic{x}.jpg", 'rb') as fphoto:
                        client.send_message(dialog_id, get_post_text(x), file = fphoto)
                        log_a_note(f"POST#{x}_CHANNEL {dialog_id} WITH PIC SUCCESSFUL")
                    except Exception as e:
                      client.send_message(dialog_id, get_post_text(x))
                      log_a_note(f"POST#{x}_CHANNEL {dialog_id} WITHOUT PIC SUCCESSFUL")
                      print("sended")
            except Exception as e:
              pass
              # raise e
        if no_post:
          last_time = datetime.datetime.now()
          curr_time = datetime.datetime.now()
          delay = randint(int(interval_low.value), int(interval_high.value))
          delta = curr_time - last_time
          while delta.seconds < delay:
            curr_time = datetime.datetime.now()
            delay = randint(int(interval_low.value), int(interval_high.value))
            delta = curr_time - last_time
            time.sleep(0.5)
      pass

def bot(limit, stop, interval_low, interval_high, posts, token, recheck):
  import time
  import emojis
  import requests
  import json
  global logger
  bot = telebot.TeleBot(token)
  msg_list = []
  admin_id = config["Posts"]["admin_id"]
  @bot.message_handler(commands=['stop'])
  def start_stop(message):
    if str(message.chat.id) == str(admin_id):
      stop.value = 0
      bot.send_message(message.chat.id, "Рассылка остановлена")

  @bot.message_handler(commands=['go'])
  def start_stop(message):
    if str(message.chat.id) == str(admin_id):
      stop.value = 1
      bot.send_message(message.chat.id, "Рассылка запущена")
  @bot.message_handler(commands=['start'])
  def send_welcome(message):
    global msg_list
    if str(message.chat.id) == str(admin_id):
      msg_list = []
      try:
          for x in range(0,limit.value):
            if posts[x] == 0:
              msg_id = bot.send_message(message.chat.id, get_post_text(x)).message_id
              msg_list.append(msg_id)
              time.sleep(0.1)
          print(msg_list)
      except Exception as e:
        bot.send_message(message.chat.id, e, entities = None)
        pass

  @bot.message_handler(commands=['interval'])
  def set_interval(message):
    if str(message.chat.id) == str(admin_id):
      try:
        low_lim = int(message.text.split(" ")[1])  * 60 + 30
        high_lim = int(message.text.split(" ")[2])  * 60 + 30
        if high_lim < low_lim:
          high_lim, low_lim = low_lim, high_lim
        interval_low.value = low_lim
        interval_high.value = high_lim
        bot.send_message(message.chat.id, "Интервал изменён успешно.")
      except Exception as e:
        print(e)
        bot.send_message(message.chat.id, "Error.Try again!")

  @bot.message_handler(commands=['lim'])
  def set_len(message):
    if str(message.chat.id) == str(admin_id):
      try:
        limit.value = int(message.text.split(" ")[1])
        bot.send_message(message.chat.id, "Лимит изменён успешно.")

      except Exception as e:
        bot.send_message(message.chat.id, "Error.Try again!")
      

  @bot.message_handler(content_types= ["photo"])
  def echo_photo(message):
    global msg_list
    try:
      if message.reply_to_message.message_id in msg_list:
        chat_id = message.chat.id
        file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)
        print(file_info)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(f"pic{msg_list.index(message.reply_to_message.message_id)}.jpg", 'wb') as new_file:
          new_file.write(downloaded_file)
        bot.send_message(message.chat.id, "Изображение изменено успешно")
    except Exception as e:
      print(e)
      bot.send_message(message.chat.id, "Error.Try again!")

  def parse_message(message):
    res_text = ""
    entities = []
    for entity in message.entities:
      print(entity)
      if entity.type == 'text_link':
        entities.append([int(entity.offset), int(entity.length), entity.url])
    text = str(emojis.decode(message.text))
    text = message.text
    diff_coeff = 0
    res_text = text
    diff = 0
    corrector = 0
    for x in entities:
      offset, length, url = x
      diff = emojis.count(text[:offset + diff])
      keyword = 0
      len_ = len(url)
      text1 = text[offset-diff:offset+length-diff]
      res_text = text[:offset-diff+corrector] + f"[{text1}]({url})" + text[offset+length-diff+corrector:]
      corrector += 3 + len_
    return res_text

  @bot.message_handler(func=lambda message: True)
  def echo_all(message):
    global msg_list
    len_diff = 0
    try:
      if message.reply_to_message.message_id in msg_list:
        text = message.text
        if text == "delete":
          try:
            try:
              os.remove(f"pic{msg_list.index(message.reply_to_message.message_id)}.jpg")
            except Exception as e:
              pass
            os.remove(f"text{msg_list.index(message.reply_to_message.message_id)}.pkl")
          except Exception as e:
            pass
          bot.reply_to(message, "Пост удалён успешно")
        elif message.entities:
          text = parse_message(message)
          with open(f"text{msg_list.index(message.reply_to_message.message_id)}.pkl", 'wb') as f:
            pickle.dump(text, f)
          recheck.value = 1
          bot.reply_to(message, "Текст заменён успешно")
          print('text done')
        else:
          print(text)
          with open(f"text{msg_list.index(message.reply_to_message.message_id)}.pkl", 'wb') as f:
            pickle.dump(text, f)
          recheck.value = 1
          print('text done')
          bot.reply_to(message, "Текст заменён успешно")
          pass
    except Exception as e:
      pass
  bot.polling()



if __name__ == '__main__':
  if WANNA_ACTIVATE_PHONES_BEFORE_USING:
    print("Активация аккаунтов")
    sender(limit, stop, interval_low, interval_high, posts)
  else:
    print("working")
    p = multiprocessing.Process(target=sender, args = (limit, stop, interval_low, interval_high, posts))
    p.start()
    # sender(limit, stop, interval_low, interval_high, posts, logger)
    p1 = multiprocessing.Process(target=bot, args = (limit, stop, interval_low, interval_high, posts, bot_token, recheck))
    p1.start()
