from flask import Flask, render_template

from admin import admin_config
from app_routes import admin_config_tab, league_config_tab, playerboard_tab, league_selector, messages_tab, matches_tab
from backend import slack

app = Flask(__name__, template_folder="./build", static_folder="./build/static")
app.register_blueprint(admin_config_tab.admin_api)
app.register_blueprint(league_config_tab.league_config_api)
app.register_blueprint(playerboard_tab.playerboard_api)
app.register_blueprint(league_selector.league_selector_api)
app.register_blueprint(messages_tab.messages_api)
app.register_blueprint(matches_tab.matches_api)


def _get_slack_client():
    slack_client = slack.LeagueSlackClient(admin_config.get_current_league())
    return slack_client


@app.route('/')
def serve_fronted():
    return render_template("index.html")


if __name__ == '__main__':
    app.run()
