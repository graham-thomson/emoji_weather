import urllib.request
import urllib.parse
import os
import json
import time
import logging

class EmojiWeather(object):

    def __init__(self, api_key, zip_code, country_code="us"):
        self.api_key = api_key
        self.zip_code = zip_code
        self.country_code = country_code

        self.cache_file = ".emoji_weather_cache"

        logging.basicConfig(
            filename="emoji_weather.log", 
            format="%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S",
            level=logging.INFO
            )

    def get_current_weather(self):

        req_time = round(time.time())

        if os.path.isfile(self.cache_file):
            logging.info(f"Found cached file: {self.cache_file}...")
            with open(self.cache_file, "r") as cache:
                cached_weather = json.load(cache)
                cached_weather_time = int(list(cached_weather.keys()).pop())

                if (req_time - cached_weather_time) < 1800:
                    logging.info("Recently checked weather, returning cached results...")
                    current_weather = cached_weather.get(str(cached_weather_time))
                    return current_weather

        logging.info("No recent cached weather found, hitting API...")

        params = {
            "zip": f"{self.zip_code},{self.country_code}",
            "appid": self.api_key
        }

        url = f"http://api.openweathermap.org/data/2.5/weather?{urllib.parse.urlencode(params)}"
        req = urllib.request.urlopen(url)
        
        resp = json.loads(req.read().decode())

        if req.code == 200:
            with open(self.cache_file, "w") as cache:
                logging.info("Caching weather for future use...")
                json.dump({req_time: resp}, cache)

        return resp

    def current_temperature(self, unit="f"):
        current_weather = self.get_current_weather()
        temp = current_weather.get("main").get("temp")
        if unit == "f":
            return EmojiWeather.kelvin_to_f(k=temp)
        elif unit == "c":
            return EmojiWeather.kelvin_to_c(k=temp)
        else:
            return temp


    @staticmethod
    def kelvin_to_f(k):
        return (k - 273.15) * (9/5) + 32

    @staticmethod
    def kelvin_to_c(k):
        return k - 273.15


if __name__ == "__main__":

    e = EmojiWeather(
        api_key="123",
        zip_code="456"
        )

    
    # print(json.dumps(e.get_current_weather(), indent=4))
    print(e.current_temperature())
    
