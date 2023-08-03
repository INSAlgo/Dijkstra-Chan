from datetime import datetime
from base64 import standard_b64decode as b64dcd
from logging import getLogger
from os import environ
from random import choice

from utils.token_error import TokenError
from utils.client_template import Client

logger = getLogger(__name__)

languages = {"py": "python", "cpp": "C++", "c": "C", "jar": "java", "js": "javascript"}


class GithubClient(Client) :
    def __init__(self) :
        Client.__init__(self, "api.github.com/")

        logger.info("initializing github client")

        self.files: dict[str, list[str]] = {}

        try :
            self.set_token(environ["GH_TOKEN"])
        except KeyError :
            logger.error("GH_TOKEN not in environment variables")
            return
        except Exception as e :
            logger.error(e)

        err_code, msg = self.reload_repo_tree()

        if err_code :
            logger.error(msg)

        logger.info("github client initialized")
    
    def make_header(self, token: str) :
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token
        }

    def set_token(self, new_token: str) :

        self.make_header(new_token)
        
        if not self.get_w_token(route="rate_limit") :
            raise Exception(self.lr_error())
        if self.lr_status_code() == 401 :
            raise TokenError
        elif self.lr_status_code() != 200 :
            raise Exception(f"status code not OK : {self.lr_status_code()}")
        
        self.token = new_token
        environ["GH_TOKEN"] = new_token
    
    # Levenshtein distance :
    @staticmethod
    def dist(str1, str2) :
        l1, l2 = len(str1), len(str2)
        arr = [[j for j in range(l2+1)]]
        arr += [[i] + [0 for _ in range(l2)] for i in range(1, l1+1)]

        for i in range(1, l1 + 1) :
            for j in range(1, l2 + 1) :
                m = min(arr[i-1][j-1], arr[i][j-1], arr[i-1][j])
                if str1[i-1] == str2[j-1] :
                    arr[i][j] = m
                else :
                    arr[i][j] = m + 1
        
        return arr[l1][l2]

    def get_w_token(self, route: str = "", protocol: str | None = None, payload: dict[str, str] = {}) -> bool:
        return self.get(route, protocol=protocol, payload=payload, headers=self.headers)


    def get_api_rate(self) -> tuple[int, str]:
        if not self.get_w_token(route="rate_limit") :
            return 2, f"client get error for API rate : {self.lr_error()}"
        
        if self.lr_status_code() != 200 :
            return 2, f"response status code not OK : {self.lr_status_code()}"

        data = self.lr_response()
        info = data["resources"]["core"]
        used_prct = 100*info["used"]/info["limit"]

        if used_prct == 100 :
            date_time = datetime.fromtimestamp(info["reset"]).strftime("%d/%m/%Y at %H:%M:%S")
            return 1, "API rate overused, retry on " + date_time
        
        return 0, f"used {used_prct}% of API rate"
    
    
    def reload_repo_tree(self) -> tuple[int, str] :
        # Getting the first layer (a file per website) :
        if not self.get_w_token(route="repos/INSAlgo/Corrections/contents/") :
            return 3, "cannot connect to GitHub API"

        if self.lr_status_code() == 403 :
            return 2, self.get_api_rate()[1]
        
        if self.lr_status_code() != 200 :
            return 3, f"response status code not OK : {self.lr_status_code()}"
        
        sites = {dir_["name"] for dir_ in self.lr_response(json=True)}.difference({"README.md"})

        # Getting the second layer (the actual solution files) :
        errors = []

        for site in sites :

            if not self.get_w_token(route=f"repos/INSAlgo/Corrections/contents/{site}") :
                errors.append(f"client error with folder for {site} : {self.lr_error()}")
                continue
            
            resp = self.lr_response()

            if self.lr_status_code() == 403 :
                errors.append(self.get_api_rate()[1])
                continue

            if self.lr_status_code() != 200 :
                errors.append(f"status code not OK for site {site} : {self.lr_status_code()}")
                continue

            self.files[site] = [sol["name"] for sol in resp]

        err_code = 0
        msg = "reloaded solution repo structure cache"
        if errors != [] :
            err_code = 1
            msg += "\n" + '\n'.join(errors)
        else :
            msg += " without errors"
        return err_code, msg


    def search_correction(self, website: str, to_search: str) -> tuple[int, str] :        
        if website not in self.files.keys() :
            return 2, f"websites available are : {', '.join(self.files.keys())}"
        
        if to_search == "" :
            choices = []
            available = set(self.files[website])
            N = min(10, len(available))
            for _ in range(N) :
                choices.append(choice(list(available)))
                available.discard(choices[-1])
            return 1, f"{N} random files of {website} are :\n" + '\n'.join(choices)

        if to_search not in self.files[website] :
            self.files[website].sort(key=lambda s: self.dist(s, to_search))
            close_files = '\n'.join(self.files[website][:10])
            return 1, "file not found, similar files are :\n" + close_files

        if not self.get_w_token(route=f"repos/INSAlgo/Corrections/contents/{website}/{to_search}") :
            return 3, self.lr_error()
        
        if self.lr_status_code() != 200 :
            return 3, f"response status code not OK : {self.lr_status_code()}"

        data = self.lr_response(json=True)

        if self.lr_status_code() == 403 :
            return 3, self.get_api_rate()[1]
        
        if self.lr_status_code() != 200 :
            return 3, f"response status code not OK : {self.lr_status_code()}"

        try :
            raw_text = b64dcd(data["content"]).decode("utf-8")
        except Exception as e:
            return 5, f"Could not decode file : {e}"

        ext = to_search.split('.')[-1]
        if ext in languages :
            language = languages[ext]
        else :
            language = ""

        return 0, f"**Solution file found** :\n||```{language}\n{raw_text}```||"


    def get_repo_readme(self, repo: str, sub_dir: str = "") -> str :
        """
        Generic method to get the raw text of the README.md file of a repo.
        Possibility to specify a directory in the repo.
        """

        if sub_dir.strip() != "" :
            path = f"repos/INSAlgo/{repo}/contents/{sub_dir}/README.md"
        else :
            path = f"repos/INSAlgo/{repo}/contents/README.md"
        
        if not self.get(path) :
            return 3, f"cannot connect to GitHub API through `api.github.com/{path}`"
        
        resp = self.lr_response()

        if self.lr_status_code() == 403 :
            return 2, self.get_api_rate()[1]
        
        if self.lr_status_code() != 200 :
            return 3, f"response status code not OK : {self.lr_status_code()}"

        try :
            raw_text = b64dcd(resp["content"]).decode("utf-8")

            return 0, raw_text
        
        except Exception as err:
            return 4, f"could not decode file : {err}"


    # Methods to get the ressources for a lesson.
    def get_INSAlgo_repos(self) -> tuple[int, str | list[str]] :
        headers = {"type": "public", "sort": "pushed", "per_page": '20'}

        if not self.get_w_token("orgs/INSAlgo/repos", payload=headers) :
            return 1, self.lr_error()
        
        if self.lr_status_code() != 200 :
            return 1, f"response status code not OK : {self.lr_status_code()}"

        data = self.lr_response(json=True)

        names = []
        for repo in data :
            if "name" in repo.keys() :
                names.append(repo["name"])

        return 0, names

    def get_INSAlgo_lessons(self, repo: str) -> tuple[int, str | list[str]] :
        if not self.get_w_token(route=f"repos/INSAlgo/{repo}/contents/") :
            return 3, "cannot connect to GitHub API"

        if self.lr_status_code() == 403 :
            return 2, self.get_api_rate()[1]
        
        if self.lr_status_code() != 200 :
            return 3, f"response status code not OK : {self.lr_status_code()}"
        
        return 0, [dir_["name"] for dir_ in self.lr_response(json=True)]

    def get_lesson_ressource(self, repo: str = "", lesson: str = "") -> tuple[int, str] :
        if repo == "" :
            err_code, res = self.get_INSAlgo_repos()
        
            if err_code > 0 :
                return 5, f"Could not get INSAlgo's repos :\n{res}"
            
            cur_year = datetime.today().year

            cur_name = f"INSAlgo-{cur_year-1}-{cur_year}"
            if cur_name not in res :
                cur_name = f"INSAlgo-{cur_year}-{cur_year+1}"
                if cur_name not in res :
                    return 5, "Could not find an appropriate repo for the current year. Name should be `INSAlgo-{year1}-{year2}`."
            
            repo = cur_name

        if lesson == "" :

            err_code, res = self.get_INSAlgo_lessons(repo)

            if err_code > 0 :
                return 6, f"Could not get lessons from `{repo}` :\n{res}"

            try :
                lesson = max(res, key=lambda s: int(s.split(' ')[0]))
            
            except ValueError :
                return 6, f"No valid lesson name found in `{repo}`. Check `https://github.com/INSAlgo/INSAlgo-2022-2023` for reference."
        
        return self.get_repo_readme(repo, lesson)

github_client = GithubClient()