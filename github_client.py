from base64 import standard_b64decode as b64dcd
from datetime import datetime

from token_error import TokenError
from client_template import Client
from levenshtein import dist

languages = {"py": "python", "cpp": "C++", "c": "C", "jar": "java", "js": "javascript"}

class GH_Client (Client) :
    def __init__(self, token: str) :
        super().__init__("api.github.com/")
        
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token
        }

        if not self.get(route="rate_limit") :
            raise Exception(self.lr_error())
        if self.lr_status_code() == 401 :
            raise TokenError
        elif self.lr_status_code() != 200 :
            raise Exception(f"status code not OK : {self.lr_status_code()}")

        self.files: dict[str, list[str]] = {}
    
    def get(self, route: str = "", protocol: str | None = None, payload: dict[str, str] = {}) -> bool:
        return super().get(route, protocol=protocol, payload=payload, headers=self.headers)

    def get_api_rate(self) -> tuple[int, str]:
        if not self.get(route="rate_limit") :
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
        if not self.get(route="repos/INSAlgo/Corrections/contents/") :
            return 3, "cannot connect to GitHub API"
        
        resp = self.lr_response()

        if self.lr_status_code() == 403 :
            return 2, self.get_api_rate()[1]
        
        if self.lr_status_code() != 200 :
            return 3, f"response status code not OK : {self.lr_status_code()}"
        
        sites = {dir_["name"] for dir_ in self.lr_response(json=True)}.difference({"README.md"})

        # Getting the second layer (the actual solution files) :
        errors = []

        for site in sites :

            if not self.get(route=f"repos/INSAlgo/Corrections/contents/{site}") :
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
        
        if to_search not in self.files[website] :
            self.files[website].sort(key=lambda s: dist(s, to_search))
            close_files = '\n'.join(self.files[website][:10])
            return 1, "file not found, similar files are :\n" + close_files

        if not self.get(route=f"repos/INSAlgo/Corrections/contents/{website}/{to_search}") :
            return 3, self.lr_error()
        
        if self.lr_status_code() != 200 :
            return 3, f"response status code not OK : {self.lr_status_code()}"

        data = self.lr_response(json=True)

        if "message" in data :
            return 4, self.get_api_rate()[1]

        try :
            raw_text = b64dcd(data["content"]).decode("ascii")

            ext = to_search.split('.')[-1]
            if ext in languages :
                language = languages[ext]
            else :
                language = ""

            return 0, f"**Solution file found** :\n||```{language}\n{raw_text}```||"
        
        except :
            return 5, "could not decode file"