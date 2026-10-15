# SlackLeagueBot
A bot used to create round robin seasons for matches between players via Slack.

# Developer Getting Started:
Install python 3.9 or greater

Create a new virtual environment somewhere
```
python3 -m venv venv
```

Activate your environment
```
source venv/bin/activate
```

Install dependencies
```
pip install slack-bolt
pip install slackclient
pip install Flask
pip install paramiko
pip install requests
```


Download and install node.js. Use node 16 for best compatibility

Install node modules
```
npm install
```

Build the frontend
```
npm run build
```

Run the Admin API
```
python start_api.py
```


When you're done you can exit the environment
```
exit
```
# Doubles Leagues
A league can run as doubles: two Slack users per team, teams re-formed every season.

1. Create a separate Slack app for the doubles bot (socket mode, same scopes and `app_mention` + `message` events as the singles bot) and invite it to the competition channel. Both bots can share the channel; each only answers messages that start with its own tag.
2. In the admin UI, add a new league (e.g. `smashbros_doubles`), open **Configuration**, and set **League Format** to **Doubles** before creating any season. The format locks once matches exist. Fill in that bot's Slack keys, Bot Slack User ID, competition channel and `BOT_NAME`.
3. Deploy the league. On the server, start its bot process and add a cron entry for its `run_reminders.py` next to the singles one (cron setup is manual).
4. Each season: on **Playerboard**, use **Season N Teams** to pair players, optionally name the team, and place teams in groups. Then **Create New Season** on the Matches tab.

Players report with the singles syntax and can tag any opponent: `@bot me over @anyOpponent 3-1`. Either partner can report. Match DMs go to both partners; use `@partner_user` in the match message to tag the partner.

Existing leagues: run **Update League** once after upgrading (schema v7). Singles behavior is unchanged.
