from datetime import datetime
from base64 import standard_b64decode as b64dcd
import json
from logging import getLogger
from os import environ
from random import choice

import requests

from utils.token_error import TokenError
from utils.client_template import Client

logger = getLogger(__name__)

languages = {"py": "python", "cpp": "C++", "c": "C", "jar": "java", "js": "javascript"}


class GithubClient(Client):
	def __init__(self):
		Client.__init__(self, "https://api.github.com/")

		logger.info("initializing github client")

		self.files: dict[str, list[str]] = {}

		try:
			self.set_token(environ["GH_TOKEN"])
		except KeyError:
			logger.error("GH_TOKEN not in environment variables")
			return
		except Exception as e:
			logger.error(e)

		err_code, msg = self.reload_repo_tree()

		if err_code:
			logger.error(msg)

		logger.info("github client initialized")

	def make_header(self, token: str):
		self.headers = {
			"Accept": "application/vnd.github+json",
			"Authorization": "Bearer " + token,
		}

	def set_token(self, new_token: str):

		self.make_header(new_token)

		if not self.get_w_token(route="rate_limit"):
			raise Exception(self.lr_error())
		if self.lr_status_code() == 401:
			raise TokenError
		elif self.lr_status_code() != 200:
			raise Exception(f"status code not OK : {self.lr_status_code()}")

		self.token = new_token
		environ["GH_TOKEN"] = new_token

	# Levenshtein distance :
	@staticmethod
	def dist(str1, str2):
		l1, l2 = len(str1), len(str2)
		arr = [[j for j in range(l2 + 1)]]
		arr += [[i] + [0 for _ in range(l2)] for i in range(1, l1 + 1)]

		for i in range(1, l1 + 1):
			for j in range(1, l2 + 1):
				m = min(arr[i - 1][j - 1], arr[i][j - 1], arr[i - 1][j])
				if str1[i - 1] == str2[j - 1]:
					arr[i][j] = m
				else:
					arr[i][j] = m + 1

		return arr[l1][l2]

	def get_w_token(
		self, route: str = "", payload: dict[str, str] = {}
	) -> bool:
		return self.get(route, payload=payload, headers=self.headers)

	def post_w_token(
		self, route: str = "", headers: dict = {}, data: str | None = None
	) -> bool:
		"""I'm not reimplementing this strange library, I know how to handle errors."""
		r = requests.post(self.make_url(route), headers=self.headers | headers, data=data)
		r.raise_for_status()
		return r

	def put_w_token(
		self, route: str = "", headers: dict = {}, data: str | None = None
	) -> bool:
		r = requests.put(self.make_url(route), headers=self.headers | headers, data=data)
		r.raise_for_status()
		return r

	def get_api_rate(self) -> tuple[int, str]:
		if not self.get_w_token(route="rate_limit"):
			return 2, f"client get error for API rate : {self.lr_error()}"

		if self.lr_status_code() != 200:
			return 2, f"response status code not OK : {self.lr_status_code()}"

		data = self.lr_response()
		info = data["resources"]["core"]
		used_prct = 100 * info["used"] / info["limit"]

		if used_prct == 100:
			date_time = datetime.fromtimestamp(info["reset"]).strftime(
				"%d/%m/%Y at %H:%M:%S"
			)
			return 1, "API rate overused, retry on " + date_time

		return 0, f"used {used_prct}% of API rate"

	def reload_repo_tree(self) -> tuple[int, str]:
		# Getting the first layer (a file per website) :
		if not self.get_w_token(route="repos/INSAlgo/Corrections/contents/"):
			return 3, "cannot connect to GitHub API"

		if self.lr_status_code() == 403:
			return 2, self.get_api_rate()[1]

		if self.lr_status_code() != 200:
			return 3, f"response status code not OK : {self.lr_status_code()}"

		sites = {dir_["name"] for dir_ in self.lr_response(json=True)}.difference(
			{"README.md"}
		)

		# Getting the second layer (the actual solution files) :
		errors = []

		for site in sites:

			if not self.get_w_token(route=f"repos/INSAlgo/Corrections/contents/{site}"):
				errors.append(
					f"client error with folder for {site} : {self.lr_error()}"
				)
				continue

			resp = self.lr_response()

			if self.lr_status_code() == 403:
				errors.append(self.get_api_rate()[1])
				continue

			if self.lr_status_code() != 200:
				errors.append(
					f"status code not OK for site {site} : {self.lr_status_code()}"
				)
				continue

			self.files[site] = [sol["name"] for sol in resp]

		err_code = 0
		msg = "reloaded solution repo structure cache"
		if errors != []:
			err_code = 1
			msg += "\n" + "\n".join(errors)
		else:
			msg += " without errors"
		return err_code, msg

	def search_correction(self, website: str, to_search: str) -> tuple[int, str]:
		if website not in self.files.keys():
			return 2, f"websites available are : {', '.join(self.files.keys())}"

		if to_search == "":
			choices = []
			available = set(self.files[website])
			N = min(10, len(available))
			for _ in range(N):
				choices.append(choice(list(available)))
				available.discard(choices[-1])
			return 1, f"{N} random files of {website} are :\n" + "\n".join(choices)

		if to_search not in self.files[website]:
			self.files[website].sort(key=lambda s: self.dist(s, to_search))
			close_files = "\n".join(self.files[website][:10])
			return 1, "file not found, similar files are :\n" + close_files

		if not self.get_w_token(
			route=f"repos/INSAlgo/Corrections/contents/{website}/{to_search}"
		):
			return 3, self.lr_error()

		if self.lr_status_code() != 200:
			return 3, f"response status code not OK : {self.lr_status_code()}"

		data = self.lr_response(json=True)

		if self.lr_status_code() == 403:
			return 3, self.get_api_rate()[1]

		if self.lr_status_code() != 200:
			return 3, f"response status code not OK : {self.lr_status_code()}"

		try:
			raw_text = b64dcd(data["content"]).decode("utf-8")
		except Exception as e:
			return 5, f"Could not decode file : {e}"

		ext = to_search.split(".")[-1]
		if ext in languages:
			language = languages[ext]
		else:
			language = ""

		return 0, f"**Solution file found** :\n||```{language}\n{raw_text}```||"

	def get_repo_readme(self, repo: str, sub_dir: str = "") -> str:
		"""
		Generic method to get the raw text of the README.md file of a repo.
		Possibility to specify a directory in the repo.
		"""

		if sub_dir.strip() != "":
			path = f"repos/INSAlgo/{repo}/contents/{sub_dir}/README.md"
		else:
			path = f"repos/INSAlgo/{repo}/contents/README.md"

		if not self.get(path):
			raise Exception(
				f"cannot connect to GitHub API through `api.github.com/{path}`"
			)

		resp = self.lr_response()

		if self.lr_status_code() == 403:
			raise Exception(self.get_api_rate()[1])

		if self.lr_status_code() != 200:
			raise Exception(f"response status code not OK : {self.lr_status_code()}")

		try:
			raw_text = b64dcd(resp["content"]).decode("utf-8")

			return raw_text

		except Exception as err:
			raise Exception(f"could not decode file : {err}")

	def create_branch(self, repo: str, base:str, new_branch: str) -> None:
		# Get the SHA of the base branch
		base_branch_url = f'https://api.github.com/repos/{repo}/git/refs/heads/{base}'
		
		r = self.get_w_token(base_branch_url)
		response = self.lr_response()
		# response = requests.get(base_branch_url, headers={'Authorization': f'token {token}'}).json()

		base_branch_sha = response['object']['sha']

		# Create the new branch
		create_branch_url = f'https://api.github.com/repos/{repo}/git/refs'
		payload = {
			"ref": f"refs/heads/{new_branch}",
			"sha": base_branch_sha
		}
		try:
			# response = requests.post(create_branch_url, json=payload, headers={'Authorization': f'token {token}'})
			response = self.post_w_token(create_branch_url, data=json.dumps(payload))
		except requests.HTTPError as http_err:
			if http_err.response.status_code == 422:
				# Branch already exists, ignore
				return

			raise


	def create_file(self, repo: str, branch: str, path: str, message: str, content: str) -> None:
		route = f"repos/{repo}/contents/{path}"

		headers = {
			"Accept": "application/vnd.github+json",
			"X-GitHub-Api-Version": "2022-11-28",
		}

		payload = {
			"message": message,
			"content": content,
			"branch": branch
		}

		try:
			r = self.put_w_token(route, headers=headers, data=json.dumps(payload))
		except requests.HTTPError as http_err:
			if http_err.response.status_code == 422:
				# File already exists, ignore
				return

			raise

	def create_pull_request(self, repo: str, base: str, new_branch: str, desc: str, file_path: str, file_content: str) -> None:
		try:
			self.create_branch(repo, base, new_branch)
			self.create_file(repo, new_branch, file_path, desc, file_content)
		except Exception as e:
			logger.error(e)
			raise

		route = f"repos/{repo}/pulls"

		headers = {
			"Accept": "application/vnd.github+json",
			"X-GitHub-Api-Version": "2022-11-28",
		}

		body = {
			"title": new_branch,
			"head": new_branch,
			"base": base,
			"body": desc,
		}

		try:
			r = self.post_w_token(route, headers=headers, data=json.dumps(body))
		except requests.HTTPError as http_err:
			logger.error(http_err)
			raise

	# Methods to get the ressources for a lesson.
	def get_INSAlgo_repos(self) -> tuple[int, str | list[str]]:
		headers = {"type": "public", "sort": "pushed", "per_page": "20"}

		if not self.get_w_token("orgs/INSAlgo/repos", payload=headers):
			return 1, self.lr_error()

		if self.lr_status_code() != 200:
			return 1, f"response status code not OK : {self.lr_status_code()}"

		data = self.lr_response(json=True)

		names = []
		for repo in data:
			if "name" in repo.keys():
				names.append(repo["name"])

		return 0, names

	def get_INSAlgo_lessons(self, repo: str) -> tuple[int, str | list[str]]:
		if not self.get_w_token(route=f"repos/INSAlgo/{repo}/contents/"):
			return 3, "cannot connect to GitHub API"

		if self.lr_status_code() == 403:
			return 2, self.get_api_rate()[1]

		if self.lr_status_code() != 200:
			return 3, f"response status code not OK : {self.lr_status_code()}"

		return 0, [dir_["name"] for dir_ in self.lr_response(json=True)]

	def find_lesson_ressource(
		self, repo: str = "", lesson: str = ""
	) -> tuple[int, str]:
		err_code, res = self.get_INSAlgo_repos()

		if err_code > 0:
			raise Exception(f"Could not get INSAlgo's repos :\n{res}")

		if repo == "":
			cur_year = datetime.today().year

			cur_name = f"INSAlgo-{cur_year}-{cur_year+1}"
			if cur_name not in res:
				cur_name = f"INSAlgo-{cur_year-1}-{cur_year}"
				if cur_name not in res:
					raise Exception(
						"Could not find an appropriate repo for the current year. Name should be `INSAlgo-{year1}-{year2}`."
					)

			repo = cur_name
		else:
			found = False
			if repo not in res and repo.isdigit():
				for repo_name in res:
					if (
						not repo_name.startswith("INSAlgo-")
						or len(repo_name.split("-")) != 3
					):
						continue

					_, year_a, year_b = repo_name.split("-")
					if int(year_a) == int(repo):
						repo = repo_name
						found = True
						break

			if not found:
				raise Exception(
					"Could not find an appropriate repo for the current year. Name should be `INSAlgo-{year1}-{year2}`."
				)

		# if lesson == "" :

		err_code, res = self.get_INSAlgo_lessons(repo)

		if err_code > 0:
			raise Exception(f"Could not get lessons from `{repo}` :\n{res}")

		if lesson == "":
			best = 0
			for l in res:
				num = l.split(" ")[0]
				if num.isdigit() and int(num) > best:
					best = int(num)
					lesson = l
		else:
			found = False
			for l in res:
				if l == lesson:
					found = True
					break
				elif lesson.isdigit():
					num = l.split(" ")[0]
					if num.isdigit() and int(num) == int(lesson):
						lesson = l
						found = True
						break

			if not found:
				raise Exception(
					f"No valid lesson name found in `{repo}`. Check `https://github.com/INSAlgo/INSAlgo-2022-2023` for reference."
				)

		return repo, lesson


github_client = GithubClient()
