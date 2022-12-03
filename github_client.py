from client_template import Client
from levenshtein import dist
from base64 import standard_b64decode as b64dcd

GH_client = Client("api.github.com/repos/")
files: dict[str, list[str]] = {}
languages = {"py": "python", "cpp": "C++", "c": "C", "jar": "java", "js": "javascript"}

def reload_repo_tree() :
    global files

    # Getting the first layer (a file per website) :
    if not GH_client.get(route="INSAlgo/Corrections/contents/") :
        return False
    resp = GH_client.lr_response(json=True)
    if "message" in resp :
        print("GitHub message :", resp["message"])
        sites = set()
    else :
        sites = {dir_["name"] for dir_ in GH_client.lr_response(json=True)}.difference({"README.md"})

    # Getting the second layer (the actual solution files) :
    for site in sites :
        if not GH_client.get(route=f"INSAlgo/Corrections/contents/{site}") :
            print("error with folder for", site)
        resp = GH_client.lr_response(json=True)
        if "message" in resp :
            print(resp["message"])
            break
        files[site] = [sol["name"] for sol in GH_client.lr_response(json=True)]
    return True

def search_correction(website: str, to_search: str) -> tuple[int, str] :
    
    if website not in files.keys() :
        return 2, f"websites available are : {', '.join(files.keys())}"
    
    if to_search not in files[website] :
        files[website].sort(key=lambda s: dist(s, to_search))
        close_files = '\n'.join(files[website][:10])
        return 1, "file not found, similar files are :\n" + close_files

    if not GH_client.get(route=f"INSAlgo/Corrections/contents/{website}/{to_search}") :
        return 3, GH_client.lr_error()
    
    data = GH_client.lr_response(json=True)
    raw_text = b64dcd(data["content"]).decode("ascii")

    language = languages[to_search.split('.')[-1]]

    return 0, f"**Solution file found** :\n```{language}\n{raw_text}```"
    
assert reload_repo_tree()

if __name__ == "__main__" :
    err_code, message = search_correction("CF", "test.py")
    print(message)