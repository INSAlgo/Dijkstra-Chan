from base64 import b64encode
from datetime import datetime, timedelta
import asyncio, re

import discord
import discord.ext.commands as cmds
from requests import HTTPError
from utils.checks import in_channel

from main import CustomBot
from utils.ids import ANNOUNCEMENT
from utils.github import github_client
from datetime import timezone, timedelta


class Website(cmds.Cog):
	"""
	Event listener for the website's blog
	"""

	@cmds.Cog.listener()
	async def on_message(self, message: discord.Message) :
		"""
		Parse every message in the annoucements channel
		"""

		if message.channel.id != ANNOUNCEMENT:
			return

		if message.author.bot:
			return

		lesson_content = message.content
		lesson_content = lesson_content.strip().split("\n", 1)
		if len(lesson_content) > 1:
			if not lesson_content[0].startswith("Bonjour les @Membres"):
				# Assume that blog posts always start with "Bonjour les @Membres"
				return

			lesson_content = lesson_content[1].strip().rsplit("\n", 1) # Remove the first line - "Bonjour les @Membres"
			if len(lesson_content) > 1:
				lesson_content = lesson_content[0] # Remove the last line - "A demain!"
			else:
				lesson_content = lesson_content[0]
		else:
			# Don't create a blog post if there is a single line
			return
		lesson_content = lesson_content.strip()


		repo = "INSAlgo/INSAlgo-Website"

		base = "main"
		new_branch = f"INSAlgo_Lesson_{datetime.now().strftime('%Y-%m-%d')}"
		title = f"{datetime.now().strftime('%Y-%m-%d')}-seance-x"
		desc = "Blog entry automatically generated from Discord!"


		# File creation
		file_path = f"_posts/{title}.md"

		event_date = datetime.now()
		while event_date.weekday() != 1:  # 1 corresponds to Tuesday
			event_date += timedelta(days=1)

		headers = {
			'layout': 'post',
			'title': f'"{title}"',
			'date': datetime.now(tz=timezone(timedelta(hours=2))).isoformat(),
			'author': f'"{message.author.display_name}"',
			'categories': 'session',
			'event-date': f'"{event_date.strftime("%d %B %Y, 18h15 - 20h")}"',
			'event-place': '"Batiment IF-501 (Ada Lovelace), salle 219"',
		}

		headers = '\n'.join([f"{k}: {v}" for k, v in headers.items()])

		content = f"---\n{headers}\n---\n\n{lesson_content}\n"
		file_content = b64encode(content.encode()).decode()


		# Pull request

		# create_pull_request(self, repo: str, base: str, new_branch: str, desc: str, file_path: str, file_content: str)

		try:
			github_client.create_pull_request(repo, base, new_branch, desc, file_path, file_content)
		except HTTPError as e:
			return

async def setup(bot: CustomBot):
	await bot.add_cog(Website(bot))
