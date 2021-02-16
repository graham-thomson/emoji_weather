import urllib.request
import urllib.parse
from urllib.error import HTTPError, URLError
import socket
import os
from pathlib import Path
import json
import time
import datetime as dt
import logging
import argparse


class EmojiWeather(object):

    def __init__(self, api_key, zip_code, country_code="us", name=None, log=None):
        self.api_key = api_key
        self.zip_code = zip_code
        self.country_code = country_code
        self.name = name
        self.log = log
        self.timeout = 5

        self.user_home = str(Path.home())
        self.cache_file = os.path.join(self.user_home, ".emoji_weather_cache")

        logging.basicConfig(
            filename=self.log, 
            format="%(asctime)s %(levelname)s %(message)s", 
            datefmt="%Y-%m-%d %H:%M:%S",
            level=logging.DEBUG if self.log else logging.INFO
            )

        self.thermometer_emoji = u"\U0001F321 "
        self.high_emoji = u'\U00002B06'
        self.low_emoji = u'\U00002B07'

        self.current_weather = self.get_current_weather()
        self.current_location = self.return_location()
        self.current_weather_emoji = self.return_weather_emoji()
        self.low_temp, self.current_temp, self.high_temp = self.current_temperature(unit="f")

    def get_current_weather(self):

        req_time = round(time.time())

        if os.path.isfile(self.cache_file):
            logging.debug(f"Found cached file: {self.cache_file}...")
            with open(self.cache_file, "r") as cache:
                cached_weather = json.load(cache).get(self.zip_code)

                if cached_weather:
                    cached_weather_time = int(list(cached_weather.keys()).pop())

                    if (req_time - cached_weather_time) < 1800:
                        logging.debug("Recently checked weather, returning cached results...")
                        current_weather = cached_weather.get(str(cached_weather_time))
                        return current_weather

        logging.debug(f"No recent cached weather found for {self.zip_code}, hitting API...")

        params = {
            "zip": f"{self.zip_code},{self.country_code}",
            "appid": self.api_key
        }

        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?{urllib.parse.urlencode(params)}"
            req = urllib.request.urlopen(url, timeout=self.timeout)
            resp = json.loads(req.read().decode())
        except HTTPError as error:
            logging.error(f"Data not returned because {error}. URL: {url}")
            return None
        except URLError as error:
            if isinstance(error.reason, socket.timeout):
                logging.error(f"Socket timed out. URL: {url}")
            else:
                logging.error(f"Other Error: {error}. URL: {url}")
            return None
        else:
            if req.code == 200:
                with open(self.cache_file, "w") as cache:
                    logging.debug("Caching weather for future use...")
                    json.dump({self.zip_code: {req_time: resp}}, cache)

            return resp

    def current_temperature(self, unit="f"):
        if not self.current_weather:
            return [None] * 3

        temp = self.current_weather.get("main").get("temp")
        high = self.current_weather.get("main").get("temp_max")
        low = self.current_weather.get("main").get("temp_min")

        temps = [low, temp, high]

        if unit == "f":
            return [EmojiWeather.kelvin_to_f(k=t) for t in temps]
        elif unit == "c":
            return [EmojiWeather.kelvin_to_c(k=t) for t in temps]
        else:
            return temps

    def return_weather_emoji(self):
        # https://unicode.org/emoji/charts/full-emoji-list.html
        # https://openweathermap.org/weather-conditions

        if not self.current_weather:
            return None
        
        t_now = round(time.time())
        sunrise = int(self.current_weather.get("sys").get("sunrise"))
        sunset = int(self.current_weather.get("sys").get("sunset"))

        weather = self.current_weather.get("weather").pop(0).get("description")

        if sunrise < t_now < sunset:
            daytime = True
        else:
            daytime = False

        weather_emoji_dict = {
                "clear sky": u"\U0001F31E" if daytime else u"\U0001F319",
                "few clouds": u"\U0001F324" if daytime else u"\U0001F319",
                "scattered clouds": u"\U000026C5" if daytime else u"\U0001F319",
                "broken clouds": u"\U000026C5" if daytime else u"\U0001F319",
                "shower rain": u"\U0001F326" if daytime else u"\U0001F319\U0001F327",
                "light rain": u"\U0001F326" if daytime else u"\U0001F319\U0001F327",
                "rain": u"\U0001F327" if daytime else u"\U0001F319\U0001F327",
                "thunderstorm": u"\U000026C8" if daytime else u"\U0001F319\U000026C8",
                "snow": u"\U00002744" if daytime else u"\U0001F319\U00002744",
                "light snow": u"\U0001F328" if daytime else u"\U0001F319\U0001F328",
                "mist": u"\U0001F326" if daytime else u"\U0001F319\U0001F327",
                "overcast clouds": u"\U00002601" if daytime else u"\U0001F319\U00002601"
        }

        weather_emoji = weather_emoji_dict.get(weather)
        if not weather_emoji:
            logging.error(f"No emoji for '{weather}'")
            return weather_emoji_dict.get("clear sky")
        return weather_emoji

    def return_location(self):
        if not self.current_weather:
            return None
        return self.current_weather.get("name")

    def return_weather_message(self):

        if self.name:
            greeting = f"Good {self.return_daypart()}, {self.name.title()}!"
        else:
            greeting = f"Good {self.return_daypart()}!"

        if self.current_weather:
            weather_message = u"\U0001F4BB " + greeting + f" It's currently {self.current_weather_emoji} " \
            + f"and {self.current_temp:.0f} degrees {self.thermometer_emoji} in {self.current_location}." \
            + f" Today: {self.high_emoji} {self.high_temp:.0f} {self.low_emoji} {self.low_temp:.0f}"
        else:
            weather_message = ""
        return weather_message

    @staticmethod
    def return_daypart(hour: int = -1) -> str:
        if hour == -1:
            hour = dt.datetime.now().hour
        if 2 < hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 22:
            return "evening"
        else:
            return "night"

    @staticmethod
    def kelvin_to_c(k: float) -> float:
        return k - 273.15

    @staticmethod
    def kelvin_to_f(k: float) -> float:
        return EmojiWeather.kelvin_to_c(k=k) * (9/5) + 32


def get_ip_location() -> dict:
    r = urllib.request.urlopen("http://ipinfo.io", timeout=5)
    return json.loads(r.read())


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=False, action="store", type=str, default=None)
    parser.add_argument("--name", required=False, action="store", type=str, default=None)
    parser.add_argument("--zip", required=False, action="store", type=str, default=None)
    parser.add_argument("--locate", required=False, action="store_true", default=False)
    parser.add_argument("--log", required=False, action="store", type=str, default=None)
    args = parser.parse_args()

    if not args.key:
        api_key = os.environ["OPEN_WEATHER_KEY"]
    else:
        api_key = args.key

    if not args.zip and args.locate:
        zip_code = get_ip_location().get("postal")
    else:
        zip_code = args.zip

    e = EmojiWeather(
        api_key=api_key,
        zip_code=zip_code,
        name=args.name,
        log=args.log
        )

    print(e.return_weather_message())