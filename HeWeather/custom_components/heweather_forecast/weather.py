"""

"""
import logging
from datetime import datetime, timedelta

import asyncio
import async_timeout
import aiohttp

import voluptuous as vol

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval

from homeassistant.components.weather import (
    WeatherEntity, ATTR_FORECAST_CONDITION, ATTR_FORECAST_TEMP,  
    ATTR_FORECAST_TEMP_LOW, ATTR_FORECAST_TIME, PLATFORM_SCHEMA)
from homeassistant.const import (ATTR_ATTRIBUTION, TEMP_CELSIUS)

import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util

_LOGGER = logging.getLogger(__name__)

TIME_BETWEEN_UPDATES = timedelta(seconds=600)

DEFAULT_TIME = dt_util.now()

CONF_CITY = "city"
CONF_APPKEY = "appkey"

CONDITION_CLASSES = {
    'sunny': ["晴"],
    'cloudy': ["多云"],
    'partlycloudy': ["少云", "晴间多云", "阴"],
    'windy': ["有风", "微风", "和风", "清风"],
    'windy-variant': ["强风", "疾风", "大风", "烈风"],
    'hurricane': ["飓风", "龙卷风", "热带风暴", "狂暴风", "风暴"],
    'rainy': ["毛毛雨", "小雨", "中雨", "大雨", "阵雨", "极端降雨"],
    'pouring': ["暴雨", "大暴雨", "特大暴雨", "强阵雨"],
    'lightning-rainy': ["雷阵雨", "强雷阵雨"],
    'fog': ["雾", "薄雾", "霾"],
    'hail': ["雷阵雨伴有冰雹"],
    'snowy': ["小雪", "中雪", "大雪", "暴雪", "阵雪"],
    'snowy-rainy': ["雨夹雪", "雨雪天气", "阵雨夹雪"],
}

ATTR_UPDATE_TIME = "更新时间"
ATTRIBUTION = "来自和风天气的天气数据"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_CITY): cv.string,
    vol.Required(CONF_APPKEY): cv.string,
})


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the hefeng weather."""
    _LOGGER.info("setup platform weather.Heweather...")

    city = config.get(CONF_CITY)
    appkey = config.get(CONF_APPKEY)

    data = WeatherData(hass, city, appkey)

    yield from data.async_update(dt_util.now())
    async_track_time_interval(hass, data.async_update, TIME_BETWEEN_UPDATES)

    async_add_devices([LocalWeather(data)], True)


class LocalWeather(WeatherEntity):
    """Representation of a weather condition."""

    def __init__(self, data):
        """Initialize the  weather."""
        self._name = None
        self._object_id = 'localweather'
        self._condition = None
        self._temperature = None
        self._temperature_unit = None
        self._humidity = None
        self._pressure = None
        self._wind_speed = None
        self._forecast = None

        self._data = data
        self._updatetime = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._object_id

    @property
    def registry_name(self):
        """返回实体的friendly_name属性."""
        return '{} {}'.format('和风天气', self._name)

    @property
    def should_poll(self):
        """attention No polling needed for a demo weather condition."""
        return True

    @property
    def temperature(self):
        """Return the temperature."""
        return self._temperature

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._temperature_unit

    @property
    def humidity(self):
        """Return the humidity."""
        return self._humidity

    @property
    def wind_speed(self):
        """Return the wind speed."""
        return self._wind_speed

    @property
    def pressure(self):
        """Return the pressure."""
        return self._pressure

    @property
    def condition(self):
        """Return the weather condition."""
        return [k for k, v in CONDITION_CLASSES.items() if
                self._condition in v][0]

    @property
    def attribution(self):
        """Return the attribution."""
        return 'Powered by Home Assistant'

    @property
    def device_state_attributes(self):
        """设置其它一些属性值."""
        if self._condition is not None:
            return {
                ATTR_ATTRIBUTION: ATTRIBUTION,
                ATTR_UPDATE_TIME: self._updatetime
            }

    @property
    def forecast(self):
        """Return the forecast."""

        reftime = datetime.now()

        forecast_data = []
        for entry in self._forecast:

            data_dict = {
                ATTR_FORECAST_TIME: reftime.isoformat(),
                ATTR_FORECAST_CONDITION: entry[0],
                ATTR_FORECAST_TEMP: entry[1],
                ATTR_FORECAST_TEMP_LOW: entry[2]
            }
            reftime = reftime + timedelta(days=1)
            forecast_data.append(data_dict)

        return forecast_data

    @asyncio.coroutine
    def async_update(self, now=DEFAULT_TIME):
        """update函数变成了async_update."""
        self._updatetime = self._data.updatetime
        self._name = self._data.name
        self._condition = self._data.condition
        self._temperature = self._data.temperature
        self._temperature_unit = self._data.temperature_unit
        self._humidity = self._data.humidity
        self._pressure = self._data.pressure
        self._wind_speed = self._data.wind_speed
        self._forecast = self._data.forecast
        _LOGGER.info("success to update informations")


class WeatherData():
    """天气相关的数据，存储在这个类中."""

    def __init__(self, hass, city, appkey):
        """初始化函数."""
        self._hass = hass

        self._url = "https://way.jd.com/he/freeweather"
        self._params = {"city": city,
                        "appkey": appkey}

        self._name = None
        self._condition = None
        self._temperature = None
        self._temperature_unit = None
        self._humidity = None
        self._pressure = None
        self._wind_speed = None
        self._forecast = None
        self._updatetime = None

    @property
    def name(self):
        """地点."""
        return self._name

    @property
    def condition(self):
        """天气情况."""
        return self._condition

    @property
    def temperature(self):
        """温度."""
        return self._temperature

    @property
    def temperature_unit(self):
        """温度单位."""
        return TEMP_CELSIUS

    @property
    def humidity(self):
        """湿度."""
        return self._humidity

    @property
    def pressure(self):
        """气压."""
        return self._pressure

    @property
    def wind_speed(self):
        """风速."""
        return self._wind_speed

    @property
    def forecast(self):
        """预报."""
        return self._forecast

    @property
    def updatetime(self):
        """更新时间."""
        return self._updatetime

    @asyncio.coroutine
    def async_update(self, now):
        """从远程更新信息."""
        _LOGGER.info("Update from JingdongWangxiang's OpenAPI...")

        """
        # 异步模式的测试代码
        import time
        _LOGGER.info("before time.sleep")
        time.sleep(40)
        _LOGGER.info("after time.sleep and before asyncio.sleep")
        asyncio.sleep(40)
        _LOGGER.info("after asyncio.sleep and before yield from asyncio.sleep")
        yield from asyncio.sleep(40)
        _LOGGER.info("after yield from asyncio.sleep")
        """

        # 通过HTTP访问，获取需要的信息
        # 此处使用了基于aiohttp库的async_get_clientsession
        try:
            session = async_get_clientsession(self._hass)
            with async_timeout.timeout(15, loop=self._hass.loop):
                response = yield from session.post(
                    self._url, data=self._params)

        except(asyncio.TimeoutError, aiohttp.ClientError):
            _LOGGER.error("Error while accessing: %s", self._url)
            return

        if response.status != 200:
            _LOGGER.error("Error while accessing: %s, status=%d",
                          self._url,
                          response.status)
            return

        result = yield from response.json()

        if result is None:
            _LOGGER.error("Request api Error")
            return
        elif result["code"] != "10000":
            _LOGGER.error("Error API return, code=%s, msg=%s",
                          result["code"],
                          result["msg"])
            return

        # 根据http返回的结果，更新数据
        all_result = result["result"]["HeWeather5"][0]
        self._temperature = float(all_result["now"]["tmp"])
        self._humidity = int(all_result["now"]["hum"])
        self._name = all_result["basic"]["city"]
        self._condition = all_result["now"]["cond"]["txt"]
        self._pressure = int(all_result["now"]["pres"])
        self._wind_speed = float(all_result["now"]["wind"]["spd"])
        self._updatetime = all_result["basic"]["update"]["loc"]
        datemsg = all_result["daily_forecast"]
        
        forec_cond = []
        for n in range(7):
            for i, j in CONDITION_CLASSES.items():
                if datemsg[n]["cond"]["txt_d"] in j:
                    forec_cond.append(i)

        self._forecast = [
            [forec_cond[0], int(datemsg[0]["tmp"]["max"]), int(datemsg[0]["tmp"]["min"])],
            [forec_cond[1], int(datemsg[1]["tmp"]["max"]), int(datemsg[1]["tmp"]["min"])],
            [forec_cond[2], int(datemsg[2]["tmp"]["max"]), int(datemsg[2]["tmp"]["min"])],
            [forec_cond[3], int(datemsg[3]["tmp"]["max"]), int(datemsg[3]["tmp"]["min"])],
            [forec_cond[4], int(datemsg[4]["tmp"]["max"]), int(datemsg[4]["tmp"]["min"])],
            [forec_cond[5], int(datemsg[5]["tmp"]["max"]), int(datemsg[5]["tmp"]["min"])],
            [forec_cond[6], int(datemsg[6]["tmp"]["max"]), int(datemsg[6]["tmp"]["min"])]]
        _LOGGER.info("success to load local informations")
