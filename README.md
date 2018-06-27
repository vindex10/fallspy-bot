fallspy_bot
-----------

* Create group in Telegram and add [@fallspy_bot](http://t.me/fallspy_bot) as a memeber.
* Call `/init` when ready
* Now, each player has to get in touch with the bot in private messaging for authentication by providing secret phrase

Play:

* Call `/go` to receive roles in PM.
* Call `/show` when finished to reveal the location and the spy.

Info:

* Call `/playlist` to show recent list of players
* Call `/loclist` to list locations.
* To update locations call `/setlocs loc1 loc2 loc3 …`

Deinit:

* It is highly recommended to `/deinit` manually, to keep bot's memory clean :)
* Session closes automatically in 24h after `/init` was called.
