Heimerdinger is a open source league of legends discord bot. The setup is fairly easy:

- Take a look into the .env file. Here you have to insert some personal data (tokens, keys, etc.)
- You will need a discord bot and its token, a riot api key and a discord channel id
- You can simply run this bot by starting the Heimerdinger.py an letting it run on your local machine
- I would recommend you setting this bot up on Heroku.com
- Try out !add [summonerName] in your discord once your script is running
- Now you should see the added League Account with !list
- Add more or remove already existing one with !remove
- If somebody in this list finishes a game, the bot will print a message into the designated channel (given channel id)
- You can trigger a message manually by typing !game [summonerName]