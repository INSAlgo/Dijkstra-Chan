from client_template import Client

CF_client = Client("api.github.com/repos/")
sites = ["CF"]

def search_correction(website: str, to_search: str) -> tuple[int, str] :
    
    if website not in sites :
        return 1, f"website {website} is not referenced (or misspelled)"

    if not CF_client.get(route="INSAlgo/Corrections") :
        return 2, CF_client.lr_error()