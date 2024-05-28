import requests

url = "https://test-app.nzilafinance.com/nza/bmx"
types = "10"
bizline = "3"
bizchannel = "KzCredito"
language = "pu"
verson = "1.0.0"

cnotent = requests.post(url=url,
                        headers= {
                            "Accept-Language": language,
                            "version": verson,
                            "b": bizchannel,
                            "bizLine": bizline,
                        },
                        json= {"types": types}).content;
print(str(cnotent, encoding="utf-8"))