# This code was mostly shamelessly stolen from my Shared Information Systems class.

import requests as r
from requests.exceptions import HTTPError, JSONDecodeError
from requests.compat import urljoin

class Client:
    def __init__(self, baseUrl: str, defaultProtocol: str = "https") :
        self.__baseUrl__ = baseUrl
        self.__defaultProtocol__ = defaultProtocol
        self.__r__ = None #Server response
        self.__error__ = None #errors

    #Changes the base url
    def set_baseurl(self, baseUrl: str) :
        self.__baseUrl__ = baseUrl

    #Creates a url out of a Client object, a route and a protocol
    def make_url(self, route: str, protocol: str | None = None) -> str :
        if protocol is None:
            protocol = self.__defaultProtocol__
        return protocol + "://" + urljoin(self.__baseUrl__, route)

    #issues an http get request
    def get(self, route: str = "", protocol: str | None = None, payload: dict[str, str] = {}, headers: dict[str, str] = {}) -> bool :
        res = True
        try :
            self.__r__ = r.get(self.make_url(route, protocol), params=payload, headers=headers)
            self.__error__ = None
        #possible errors
        except HTTPError as http_err:
            self.__error__ = f'HTTP error occurred: {http_err}'
            self.__r__ = None
            res = False
        except Exception as err:
            self.__error__ = f'Other error occurred: {err}'
            self.__r__ = None
            res = False
        return res
    

    #issues an http post request
    def post(self, route: str = "", protocol: str | None = None, data: str | None = None, headers: dict[str, str] = {}) -> bool :
        res = True
        try :
            if data is None :
                self.__r__ = r.post(self.make_url(route, protocol))
            else :
                self.__r__ = r.post(self.make_url(route, protocol), data=data, headers=headers)
            self.__error__ = None
        #possible errors
        except HTTPError as http_err:
            self.__error__ = f'HTTP error occurred: {http_err}'
            self.__r__ = None
            res = False
        except Exception as err:
            self.__error__ = f'Other error occurred: {err}'
            self.__r__ = None
            res = False
        return res

    #returns the last response to a succesful query
    def lr(self) -> r.Response | None :
        return self.__r__

    #returns the last error raised by a query
    def lr_error(self) -> str | None :
        return self.__error__

    def lr_status_code(self) -> int | None :
        res = None
        if self.__r__ != None:
            res = self.__r__.status_code
        return res

    def lr_headers(self) -> dict[str] | None :
        res = None
        if self.__r__ != None:
            res = self.__r__.headers
        return res

    def lr_response(self, json: bool = True) -> str | dict | None :
        res = None
        if self.__r__ != None:
            if json :
                try :
                    res = self.__r__.json()
                except JSONDecodeError :
                    res = "Could not decode json from response"
            else :
                res = self.__r__.text
        return res