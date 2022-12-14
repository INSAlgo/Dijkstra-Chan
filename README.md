# Setup info

To test the bot, just use github's codespace on dijkstra-chan's repo :</br>
![](README_images/codespace.png)</br>
Since the tokens are stored in github's codespace secrets, running the script this way does not require to store them locally.</br>
Whenever you need to reset a token, make sure to update it in the codespace's secrets for the bot to run properly. It's in the repo's Settings -> Security -> Secrets -> Codespaces.

If you want to run it locally, first get your hand on the tokens (ask the current admin) to add them to your environment variables.</br>
Then you can do :
- `git clone https://github.com/INSAlgo/Dijkstra-Chan.git`,
- `python -m venv env`,
- `env/Scripts/activate`,
- `pip install -r requirements.txt`,
- and finally : `python main.py`

## Discord Token
If the token was reset, you can generate a new token in the [discord developer portal](https://discord.com/developers), but someone will need to give you authorizations, so ask for the previous head of INSAlgo on the discord server (they should still be "ancients").</br>
To give authorization to a new bureau, select the team "Dijkstra-Chan administrators" in the "Teams" tab, then invite new members. You can also transfer team ownership to the new head of INSAlgo.

## GitHub Token
For the bot to access the repository with exercise corrections, you'll need an access token to give him (else he only has 60 queries per hour). Here is a tutorial on how to set it up :
- You need to be an administrator of the association INSAlgo on GitHub.
- Go to your profile's Settings -> Developer settings -> Fine-grained tokens.
- Select "Generate new token".
- Fill these settings (change the expiration date to the end of your mandate) :</br>
![](README_images/github.png)
- Then, in the permissions, choose "Contents".
- You can now generate the token and copy the string given, paste it somewhere safe now to avoid losing it.