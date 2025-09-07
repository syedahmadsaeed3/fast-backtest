import sys
import threading
from threading import Lock


class BackgroundProcess(threading.Thread):
    def __init__(self, *args, **keywords):
        threading.Thread.__init__(self, *args, **keywords)
        self.killed = False

    def start(self):
        self.__run_backup = self.run
        self.run = self.__run
        threading.Thread.start(self)

    def __run(self):
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup

    def globaltrace(self, frame, event, arg):
        if event == 'call':
            return self.localtrace
        else:
            return None

    def localtrace(self, frame, event, arg):
        if self.killed:
            if event == 'line':
                raise SystemExit()
        return self.localtrace

    def kill(self):
        self.killed = True


class SingletonMeta(type):
    """
    This is a thread-safe implementation of Singleton.
    """

    _instances = {}

    _lock: Lock = Lock()
    """
    We now have a lock object that will be used to synchronize threads during
    first access to the Singleton.
    """

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        # Now, imagine that the program has just been launched. Since there's no
        # Singleton instance yet, multiple threads can simultaneously pass the
        # previous conditional and reach this point almost at the same time. The
        # first of them will acquire lock and will proceed further, while the
        # rest will wait here.
        with cls._lock:
            # The first thread to acquire the lock, reaches this conditional,
            # goes inside and creates the Singleton instance. Once it leaves the
            # lock block, a thread that might have been waiting for the lock
            # release may then enter this section. But since the Singleton field
            # is already initialized, the thread won't create a new object.
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class UserThread(metaclass=SingletonMeta):

    user_data = {}

    def __init__(self):
        self.user_data = {}

    def get_user_data(self, user_id):
        if user_id in self.user_data:
            return self.user_data[user_id]
        else:
            return None

    def initialize_user(self, user_id):
        if user_id not in self.user_data:
            self.user_data[user_id] = {}

    def delete_user_data(self, user_id):
        if user_id in self.user_data:
            del self.user_data[user_id]
        else:
            return None

    def get_user_data_by_key(self, user_id, key):
        if user_id in self.user_data:
            if key in self.user_data[user_id]:
                return self.user_data[user_id][key]
            else:
                return None
        else:
            return None

    def set_user_data_by_key(self, user_id, key, data):
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        self.user_data[user_id].update({key: data})

    def delete_user_data_by_key(self, user_id, key):
        if user_id in self.user_data:
            if key in self.user_data[user_id]:
                del self.user_data[user_id][key]
            else:
                return None
            return None
        else:
            pass


class PriceCache(metaclass=SingletonMeta):

    prices = {}

    def __init__(self):
        self.prices = {}

    def get_price(self, symbol):
        if symbol in self.prices:
            return self.prices[symbol]
        else:
            return None

    def set_price(self, symbol, price):
        # loop and set all dates to price
        if symbol not in self.prices:
            self.prices[symbol] = {}
        for p in price:
            self.prices[symbol][p.timestamp] = p

    def get_price_at_date(self, symbol, date):
        if symbol in self.prices:
            if date in self.prices[symbol]:
                return self.prices[symbol][date]
            else:
                return None
        else:
            return None

    def get_last_price(self, symbol):
        if symbol in self.prices:
            return self.prices[symbol][max(self.prices[symbol].keys())]
        else:
            return None

    def get_last_price_date(self, symbol):
        if symbol in self.prices:
            return max(self.prices[symbol].keys())
        else:
            return None

    def get_prices_in_date_range(self, symbol, start_date, end_date):
        if symbol in self.prices:
            prices = []
            for date in self.prices[symbol]:
                if date >= start_date and date <= end_date:
                    prices.append(self.prices[symbol][date])
            return prices
        else:
            return None

    def get_prices_from_date(self, symbol, start_date):
        if symbol in self.prices:
            prices = []
            for date in self.prices[symbol]:
                if date >= start_date:
                    prices.append(self.prices[symbol][date])
            return prices
        else:
            return None

    def set_price_at_date(self, symbol, date, price):
        if symbol not in self.prices:
            self.prices[symbol] = {}
        self.prices[symbol][date] = price
        return None