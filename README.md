# Dijkstra-Chan

INSAlgo's friendly Discord bot. He can play with you, help you with algorithms, remind you of contests, and more. He also has the ability to get annoying by repeating what you say.

# Setup

## Local

If you want to run it locally, first get your hand on the tokens (ask the current admin) to add them to your environment variables.

Then you can do :

 - `git clone https://github.com/INSAlgo/Dijkstra-Chan.git`
 - `python -m venv env`
 - `source env/bin/activate` (Linux) or `env/Scripts/activate` (Windows)
 - `pip install -r requirements.txt`
 - `python main.py`

If you want to add new games, just clone them in the `games` folder.

## Deploy on the VPS

The normal way to deploy the bot is with the GitHub action. It runs automatically when a commit is pushed on the master branch, but you can trigger it manually on any branch from the "Actions" panel.

## Debug on the VPS

 - `ssh <adresse>`
 - input password
 - `cd Dijkstra-Chan/`
 - logs are in `bot.log`

Games updates must be pulled manually (submodules are a pain, please don't try it again).

## Discord Token

If for some reason you need a new token, you can generate one on the [discord developer portal](https://discord.com/developers). You will need the authorization, that you can ask from the previous admins.

To give authorization to new people, select the team "Dijkstra-Chan administrators" in the "Teams" tab, then invite new members. You can also transfer team ownership.

## GitHub Token

For the bot to access the repository with exercise corrections, you'll need to provide an access token (else he only has 60 queries per hour). If you need a new one, you can do so from settings of INSAlgo's GitHub organisation page.
