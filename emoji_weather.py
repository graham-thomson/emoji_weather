import urllib.request
import urllib.parse
import os
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

        self.cache_file = ".emoji_weather_cache"

        logging.basicConfig(
            filename=self.log, 
            format="%(asctime)s %(levelname)s %(message)s", 
            datefmt="%Y-%m-%d %H:%M:%S",
            level=logging.DEBUG if self.log else logging.INFO
            )

        self.thermometer_emoji = u"\U0001F321 "
        self.high_emoji = u'\U00002B06'
        self.low_emoji = u'\U00002B07'

        self.current_temp = None
        self.high_temp = None
        self.low_temp = None

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

        url = f"http://api.openweathermap.org/data/2.5/weather?{urllib.parse.urlencode(params)}"
        req = urllib.request.urlopen(url)
        
        resp = json.loads(req.read().decode())

        if req.code == 200:
            with open(self.cache_file, "w") as cache:
                logging.debug("Caching weather for future use...")
                json.dump({self.zip_code: {req_time: resp}}, cache)

        return resp


    def current_temperature(self, unit="f"):
        current_weather = self.get_current_weather()
        temp = current_weather.get("main").get("temp")
        high = current_weather.get("main").get("temp_max")
        low = current_weather.get("main").get("temp_min")

        self.current_temp = temp
        self.high_temp = high
        self.low_temp = low

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


    def return_weather_message(self):

        if self.name:
            greeting = f"Good {self.return_daypart()}, {self.name.title()}!"
        else:
            greeting = f"Good {self.return_daypart()}!"

        return u"\U0001F4BB " + greeting + f" It's currently {self.return_weather_emoji()} " \
        + f"and {self.current_temperature():.0f} degrees {self.thermometer_emoji} in {self.return_location()}." \
        + f" Today: {self.high_emoji} {EmojiWeather.kelvin_to_f(self.high_temp):.0f} {self.low_emoji} {EmojiWeather.kelvin_to_f(self.low_temp):.0f}"

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


def get_ip_location():
    r = urllib.request.urlopen("http://ipinfo.io")
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
    
