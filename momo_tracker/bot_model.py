from line import Bot
from playwright.async_api import Browser


class MomoTrackerBot(Bot):
    browser: Browser
