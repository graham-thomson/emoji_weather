import urllib.request
import urllib.parse
import os
import json
import time
import datetime as dt
import logging
import argparse


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

        self.thermometer_emoji = u"\U0001F321 "

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


    def return_weather_emoji(self):
        # https://unicode.org/emoji/charts/full-emoji-list.html
        # https://openweathermap.org/weather-conditions

        current_weather = self.get_current_weather()
        
        t_now = round(time.time())
        sunrise = int(current_weather.get("sys").get("sunrise"))
        sunset = int(current_weather.get("sys").get("sunset"))

        weather = current_weather.get("weather").pop(0).get("description")

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
                "snow": u"\U0001F328" if daytime else u"\U0001F319\U0001F328",
                "mist": u"\U0001F326" if daytime else u"\U0001F319\U0001F327"
        }

        return weather_emoji_dict.get(weather)


    def return_location(self):
        current_weather = self.get_current_weather()
        return current_weather.get("name")

    @staticmethod
    def return_daypart(hour=-1):
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
    def kelvin_to_c(k):
        return k - 273.15

    @staticmethod
    def kelvin_to_f(k):
        return EmojiWeather.kelvin_to_c(k=k) * (9/5) + 32


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=False, action="store", default=None)
    parser.add_argument("--name", required=False, action="store", default=None)
    parser.add_argument("--zip", required=False, action="store", default="02108")
    args = parser.parse_args()

    if not args.key:
        api_key = os.environ["OPEN_WEATHER_KEY"]
    else:
        api_key = args.key

    e = EmojiWeather(
        api_key=api_key,
        zip_code=args.zip
        )

    print(f"Good {e.return_daypart()}! It's currently {e.return_weather_emoji()} and {e.current_temperature():.0f} degrees {e.thermometer_emoji} in {e.return_location()}.")
    
