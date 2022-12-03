# Setup info

To run the bot, you'll need tokens (information on how to get them bellow) that you need to pass as arguments of the terminal command `python main.py`.</br>
You can also store these tokens in local files (make sure to have them ignored by git, else they might get automatically reset by discord and github).</br>
For more information on how to pass the arguments, use `python main.py -h`

## Discord Token
If the token was reset, you can generate a new token in the [discord developer portal](https://discord.com/developers), but I, the creator, will need to give you authorizations, so ask for leroymilo#0792 on INSAlgo's discord server (I should still be an "ancient").

## GitHub Token
For the bot to access the repository with exercise corrections, you'll need an access token to give him (else he only has 60 queries per hour). Here is a tutorial on how to set it up :</br>
You need to be an administrator of the association INSAlgo on GitHub.</br>
Go to your profile's Settings -> Developer settings -> Fine-grained tokens.</br>
Select "Generate new token".</br>
Fill these settings (change the expiration date to the end of your mandate) :</br>
![](README_images/github.png)</br>
Then, in the permissions, choose "Contents".</br>
You can now generate the token and copy the string given, paste it somewhere safe now to avoid losing it.