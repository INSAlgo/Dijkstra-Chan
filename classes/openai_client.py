from os import getenv

import openai

# from classes.token_error import TokenError

# A python class to use openai API with the openai python library :
class OPENAI_Client :
    def __init__(self, token: str) :
        openai.organization = "org-LRKugr0Z6ZFbnFoYNXR0433F"
        openai.api_key = token
    
    def complete(self, prompt: str, user: str, temp: float = 0.6, max_tks: int = 250) :
        """
        Lets openai complete the given prompt
        """
        response = openai.Completion.create(
            model="code-davinci-002",
            prompt=prompt,
            temperature=temp,
            max_tokens=max_tks,
            user=user
        )
        return response.choices[0].text

    def insert(self, suffix: str, prefix: str) :
        """
        Lets openai create code between the suffix and the prefix given
        """


if __name__ == "__main__" :
    oai_client = OPENAI_Client(getenv("OPENAI_TOKEN"))
    print(oai_client.complete("def mean(l: list[float]) :", ""))