import telebot.creds as creds
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import requests
import datetime
import json

from os import environ
from flask import Flask

app = Flask(__name__)
app.run(environ.get('PORT'))

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

PIN = "110001"
url_base = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/findByPin?pincode=" + PIN + "&date="


def sendMessageToUsers(session, context):
    name = session["name"]
    address = session["address"]
    vaccine = session["vaccine"]
    msg = "Slots for " + vaccine + " are available at PIN: " + PIN + " at " + name + ", " + address + "."
    context.bot.send_message(chat_id=context.job.context[0], text=msg)
    url = "https://selfregistration.cowin.gov.in/"
    msg = "Follow this link to signin: " + url
    context.bot.send_message(chat_id=context.job.context[0], text=msg)


def searchSlots(context):
    date = datetime.date.today().strftime('%d-%m-%Y')
    url = url_base + str(date)
    res = requests.get(url)
    slots_str = res.text
    slots = json.loads(slots_str)
    sent = False

    if len(slots["sessions"]) != 0:
        for session in slots["sessions"]:
            if(session["available_capacity"] > 0 and session['min_age_limit'] > 17 and session['min_age_limit'] < 100):
                sendMessageToUsers(session, context)
                sent = True
    
    if(sent == True):
        context.job.schedule_removal()
        context.bot.send_message(chat_id=context.job.context[0], text = "To receive messages for next available slot, press /start again.")

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Hello there! This bot will update you if vaccine slots are available at 583101.')

    context.job_queue.run_repeating(searchSlots, interval=1, first=15, context=[update.message.chat_id])

def remove(update, context):
    chat_id = update.effective_chat.id
    scheduled_jobs = context.job_queue.get_jobs_by_name(chat_id)

    for job in scheduled_jobs:
        job.schedule_removal()
        print(job)
        
    
    context.bot.send_message(chat_id=update.effective_chat.id, text='Okay. I will stop alerting you. Bye!')

def main():
    """Run bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(creds.bot_token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("remove", remove))

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()