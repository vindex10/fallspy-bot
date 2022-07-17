import json
import os
import re
from random import choice
from string import ascii_letters
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram.error import TelegramError


class SpyfallBot:
    def __init__(self, config="config.cfg"):
        self.state = {}
        self.hashes = {}

        try:
            with open(config, "r", encoding="utf-8") as fin:
                config = json.load(fin)
        except FileNotFoundError:
            config = {}
            config.update({"apikey": os.environ["BOT_TOKEN"]})

        with open("README.md", "r", encoding="utf-8") as f:
            self.help_msg = f.read()

        self.app = ApplicationBuilder().token(config["apikey"]).build()

        self.app.add_handler(CommandHandler('start', self.cmd_start))
        self.app.add_handler(CommandHandler('init', self.cmd_init))
        self.app.add_handler(MessageHandler(filters.TEXT & (~ filters.COMMAND), self.cmd_default))
        self.app.add_handler(CommandHandler('setlocs', self.cmd_setlocs))
        self.app.add_handler(CommandHandler('addlocs', self.cmd_addlocs))
        self.app.add_handler(CommandHandler('loclist', self.cmd_loclist))
        self.app.add_handler(CommandHandler('playlist', self.cmd_playlist))
        self.app.add_handler(CommandHandler('go', self.cmd_go))
        self.app.add_handler(CommandHandler('show', self.cmd_show))
        self.app.add_handler(CommandHandler('deinit', self.cmd_deinit))

    def run(self):
        self.app.run_polling()

    async def cmd_start(self, update, context):
        group = update.message.chat_id
        await context.bot.send_message(chat_id=group, text=self.help_msg)

    async def cmd_init(self, update, context):
        await self.cmd_deinit(update, context, quiet=True)

        group = update.message.chat_id
        defaultlocations = ["Kitchen at the Ship",
                            "Basement of the White House",
                            "Stuck elevator at the Trump Tower",
                            "Labirinth with Minotaur",
                            "Rabbithole to the Wonderland",
                            "Loaded into the Matrix"]

        grhash = self.__genhash__()
        self.hashes.update({grhash: group})

        job = context.job_queue.run_once(self._deinit_job_callback,
                                         86400,
                                         data={"group": group,
                                               "quiet": False})

        self.state.update({group: {"players": [],
                                   "locations": defaultlocations,
                                   "thespy": "",
                                   "theloc": "",
                                   "hash": grhash,
                                   "timeout": job}})
        await context.bot.send_message(chat_id=group,
                                       text="Hi! Everyone, please forward me (@fallspy_bot) the next message "
                                            "to Private Chat for authentication . This session is active for 24h")
        await context.bot.send_message(chat_id=group, text=grhash)

    async def cmd_default(self, update, context):
        grhash = update.message.text
        uid = update.message.chat_id
        try:
            username = await self.__get_uname__(context, self.hashes[grhash], uid)
        except (TelegramError, KeyError):
            await context.bot.send_message(chat_id=update.message.chat_id,
                                           text="You are not a member of the corresponding group.")
            return
        self.state[self.hashes[grhash]]["players"].append(uid)
        await context.bot.send_message(chat_id=self.hashes[grhash], text=f"Added {username}")

    async def cmd_setlocs(self, update, context):
        group = update.message.chat_id
        try:
            argstr = " ".join(context.args)
            arglist = [re.sub('"([^"]+)"', "\\1",
                       s.group(0)) for s in re.finditer(r'("[^"]+"|[^"\s]+)', argstr)]
            self.state[group]["locations"] = arglist
            await context.bot.send_message(chat_id=group, text="New locations:")
            await self.cmd_loclist(update, context)
        except KeyError:
            await context.bot.send_message(chat_id=group, text="Call /init to initialize")
            return

    async def cmd_addlocs(self, update, context):
        group = update.message.chat_id
        try:
            argstr = " ".join(context.args)
            arglist = [re.sub('"([^"]+)"', "\\1",
                       s.group(0)) for s in re.finditer(r'("[^"]+"|[^"\s]+)', argstr)]
            self.state[group]["locations"] += arglist
        except KeyError:
            await context.bot.send_message(chat_id=group, text="Call /init to initialize")

    async def cmd_loclist(self, update, context):
        chat_id = update.message.chat_id
        try:
            await context.bot.send_message(chat_id=chat_id, text="\n".join(self.state[chat_id]["locations"]))
        except KeyError:
            await context.bot.send_message(chat_id=chat_id, text="Call /init to start.")

    async def cmd_playlist(self, update, context):
        chat_id = update.message.chat_id
        try:
            playernames = [await self.__get_uname__(context, chat_id, player)
                           for player in self.state[chat_id]["players"]]
        except KeyError:
            await context.bot.send_message(chat_id=chat_id, text="Call /init first")
            return
        except TelegramError:
            await context.bot.send_message(chat_id=chat_id, text="Outdated player list. Call /init to re-init.")
            return

        await context.bot.send_message(chat_id=chat_id, text="\n".join(playernames))

    async def cmd_go(self, update, context):
        group = update.message.chat_id

        try:
            data = self.state[group]
        except KeyError:
            await context.bot.send_message(chat_id=group, text="Call /init before start")
            return

        thespy = choice(data["players"])
        theloc = choice(data["locations"])
        data["theloc"] = theloc
        data["thespy"] = thespy

        for player in data["players"]:
            if player == thespy:
                await context.bot.send_message(chat_id=player, text="You are the SPY")
            else:
                await context.bot.send_message(chat_id=player, text=f"Location: {theloc}")

    async def cmd_show(self, update, context):
        group = update.message.chat_id
        try:
            data = self.state[group]
        except KeyError:
            await context.bot.send_message(chat_id=update.message.chat_id, text="Call /init before start")
            return

        try:
            spyname = await self.__get_uname__(context, group, data["thespy"])
        except TelegramError:
            spyname = ""
        loc = data["theloc"]

        await context.bot.send_message(chat_id=group, text=f"Spy: {spyname}\nLocation: {loc}")

    async def cmd_deinit(self, update, context, quiet=False):
        group = update.message.chat_id
        await self._deinit_group(group, context, quiet=quiet)

    async def _deinit_job_callback(self, context):
        await self._deinit_group(context.job.data["group"], context, context.job.data["quiet"])

    async def _deinit_group(self, group, context, quiet):
        try:
            timeout_job = self.state[group]["timeout"]
            timeout_job.schedule_removal()
            del self.hashes[self.state[group]["hash"]]
            del self.state[group]
        except KeyError:
            if not quiet:
                await context.bot.send_message(chat_id=group, text="Nothing to /deinit. Initialize first (/init).")
            return
        if not quiet:
            await context.bot.send_message(chat_id=group, text="Session destroyed.")

    @staticmethod
    def __genhash__():
        return "".join([choice(ascii_letters) for i in range(10)])

    async def __get_uname__(self, context, gid, uid):
        return (await context.bot.get_chat_member(gid, uid)).user.name


if __name__ == "__main__":
    _bot = SpyfallBot()
    _bot.run()
