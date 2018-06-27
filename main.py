import json
from random import choice
from string import ascii_letters
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import TelegramError

class SpyfallBot:
    def __init__(self, config="config.cfg"):
        self.state = dict()
        self.hashes = dict()


        config = json.load(open(config, "r"))
        self.listener = Updater(config["apikey"])

        self.listener.dispatcher.add_handler(CommandHandler('init', self.cmd_init\
                                                           ,pass_job_queue=True))
        self.listener.dispatcher.add_handler(MessageHandler(Filters.text, self.cmd_default))
        self.listener.dispatcher.add_handler(CommandHandler('setlocs', self.cmd_setlocs
                                            ,pass_args=True))
        self.listener.dispatcher.add_handler(CommandHandler('loclist', self.cmd_loclist))
        self.listener.dispatcher.add_handler(CommandHandler('playlist', self.cmd_playlist))
        self.listener.dispatcher.add_handler(CommandHandler('go', self.cmd_go))
        self.listener.dispatcher.add_handler(CommandHandler('show', self.cmd_show))

    def run(self):
        self.listener.start_polling()

    def cmd_init(self, bot, update, job_queue):
        self.cmd_deinit(bot, update, quiet=True)

        group = update.message.chat_id
        defaultlocations = ["Kitchen at the Ship"
                           ,"Basement of the White House"
                           ,"Stucked elevator at the Trump Tower"
                           ,"Labirinth with Minotaur"
                           ,"Rabbithole to the Wonderland"
                           ,"Loaded into the Matrix"]

        grhash = self.__genhash__()
        self.hashes.update({grhash: group})

        job = job_queue.run_once(lambda bot, job: self.cmd_deinit(bot, update), 86400)

        self.state.update({group: {"players": []
                                  ,"locations": defaultlocations
                                  ,"thespy": ""
                                  ,"theloc": ""
                                  ,"hash": grhash
                                  ,"timeout": job}})
        bot.send_message(chat_id=group, text="Hi! Everyone, please send me (@fallspy_bot) a PRIVATE message with the only text '{}' for authentication. This session is active for 24h".format(grhash))


    def cmd_default(self, bot, update):
        grhash = update.message.text
        uid = update.message.chat_id
        try:
            username = self.__get_uname__(bot, self.hashes[grhash], uid)
        except (TelegramError, KeyError):
            bot.send_message(chat_id=update.message.chat_id, text="You are not a member of the corresponding group.")
            return
        self.state[self.hashes[grhash]]["players"].append(uid)
        bot.send_message(chat_id=self.hashes[grhash], text="Added {}".format(username))

    def cmd_setlocs(self, bot, update, args):
        group = update.message.chat_id
        try:
            self.state[group]["locations"] = args
            bot.send_message(chat_id=group, text="New locations:")
            self.cmd_loclist(bot, update)
        except KeyError:
            bot.send_message(chat_id=group, text="Call /init to initialize")
            return

    def cmd_loclist(self, bot, update):
        chat_id = update.message.chat_id
        try:
            bot.send_message(chat_id=chat_id, text="\n".join(self.state[chat_id]["locations"]))
        except KeyError:
            bot.send_message(chat_id=chat_id, text="Call /init to start.")

    def cmd_playlist(self, bot, update):
        chat_id = update.message.chat_id
        try:
            playernames = [self.__get_uname__(bot, chat_id, player)\
                                for player in self.state[chat_id]["players"]]
        except KeyError:
            bot.send_message(chat_id=chat_id, text="Call /init first")
            return
        except TelegramError:
            bot.send_message(chat_id=chat_id, text="Outdated player list. Call /init to re-init.")
            return

        bot.send_message(chat_id=chat_id, text="\n".join(playernames))

    def cmd_go(self, bot, update):
        group = update.message.chat_id

        try:
            data = self.state[group]
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

    def cmd_show(self, bot, update):
        group = update.message.chat_id
        try:
            data = self.state[group]
        except KeyError:
            bot.send_message(chat_id=update.message.chat_id, text="Call /init before start")
            return
        
        try:
            spyname = self.__get_uname__(bot, group, self.state[group]["thespy"])
        except TelegramError:
            spyname = ""
        loc = self.state[group]["theloc"]

        bot.send_message(chat_id=group, text="Spy: {}\nLocation: {}".format(spyname, loc))

    def cmd_deinit(self, bot, update, quiet=False):
        group = update.message.chat_id
        try:
            self.state[group]["timeout"].schedule_removal()
            del self.hashes[self.state[group]["hash"]]
            del self.state[group]
        except KeyError:
            if not quiet:
                bot.send_message(chat_id=group, text="Nothing to /deinit. Initialize first (/init).")
            return
        if not quiet:
            bot.send_message(chat_id=group, text="Session destroyed.")

    @staticmethod
    def __genhash__():
        return "".join([choice(ascii_letters) for i in range(10)])

    def __get_uname__(self, bot, gid, uid):
        return bot.get_chat_member(gid, uid).user.name

if __name__ == "__main__":
    bot = SpyfallBot()
    bot.run()
