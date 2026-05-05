import datetime
import config

def is_market_open() -> bool:
    date_time = datetime.datetime.now()
    day = date_time.weekday()
    time = date_time.time() 

    market_time = False  
    market_day = False

    if time > config.MARKET_HOURS_START and time < config.MARKET_HOURS_END:
        market_time = True

    if day < 5:
        market_day = True        

    return market_day and market_time