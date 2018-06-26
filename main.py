from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import telegram
from random import choice
import json

def loclist(bot, update):
    chat_id = update.message.chat_id
    try:
        bot.send_message(chat_id=chat_id, text="\n".join(state[chat_id]["locations"]))
    except KeyError:
        bot.send_message(chat_id=chat_id, text="Call /init to start")

def playlist(bot, update):
    chat_id = update.message.chat_id
    try:
        playernames = [bot.get_chat_member(chat_id, player).user.name\
                            for player in state[chat_id]["players"]]
    except KeyError:
        bot.send_message(chat_id=chat_id, text="Call /init first")
        return
    except telegram.TelegramError:
        bot.send_message(chat_id=chat_id, text="Outdated player list")
        return

    bot.send_message(chat_id=chat_id, text="\n".join(playernames))

def init(bot, update):
    chat_id = update.message.chat_id
    grhash = genhash()
    hashes.update({grhash: chat_id})
    state.update({chat_id: {"players": []
                           ,"locations": defaultlocations
                           ,"thespy": ""
                           ,"theloc": ""}})
    bot.send_message(chat_id=chat_id, text="Hi! Everyone, please send me (@fallspy_bot) a PRIVATE message with only text '{}' for authentication.".format(grhash))

def default(bot, update):
    grhash = update.message.text
    if grhash in hashes.keys():
        uid = update.message.chat_id
        try:
            user = bot.get_chat_member(hashes[grhash], uid).user
        except telegram.TelegramError:
            bot.send_message(chat_id=update.message.chat_id, text="Error")
            return
        state[hashes[grhash]]["players"].append(uid)
        bot.send_message(chat_id=hashes[grhash], text="Added {}".format(user.name))

def go(bot, update):
    group = update.message.chat_id

    try:
        data = state[group]
    except KeyError:
        bot.send_message(chat_id=group, text="Call /init before start")
        return

    thespy = choice(data["players"])
    theloc = choice(data["locations"])
    data["theloc"] = theloc
    data["thespy"] = thespy

    for player in data["players"]:
        if player == thespy:
            bot.send_message(chat_id=player, text="You are the SPY")
        else:
            bot.send_message(chat_id=player, text="Location: {}".format(theloc))

def show(bot, update):
    group = update.message.chat_id
    try:
        data = state[group]
    except KeyError:
        bot.send_message(chat_id=update.message.chat_id, text="Call /init before start")
        return
    
    try:
        spyname = bot.get_chat_member(group, state[group]["thespy"]).user.name
    except:
        spyname = ""

    bot.send_message(chat_id=update.message.chat_id, text="Spy: {}\nLocation: {}".format(spyname, state[group]["theloc"]))

def genhash():
    return "".join([choice(["a", "b", "c"]) for i in range(10)])

state = dict()
hashes = dict()
defaultlocations=["a", "b", "c"]

config = json.load(open("config.cfg", "r"))

bot = Updater(config["apikey"])
bot.dispatcher.add_handler(CommandHandler('init', init))
bot.dispatcher.add_handler(CommandHandler('loclist', loclist))
bot.dispatcher.add_handler(CommandHandler('playlist', playlist))
bot.dispatcher.add_handler(CommandHandler('go', go))
bot.dispatcher.add_handler(CommandHandler('show', show))
bot.dispatcher.add_handler(MessageHandler(Filters.text, default))
bot.start_polling()
