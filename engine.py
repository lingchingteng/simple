from __future__ import annotations  # the FUTURE of annotation...hah 
from collections import defaultdict
from typing import Any, Dict, List, Callable
from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime
from dataclasses import dataclass
from time import sleep
import logging
from threading import Thread


LOG = logging.getLogger(__name__)
logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logging.getLogger().addHandler(consoleHandler)
LOG.setLevel(logging.DEBUG)

# Basic Data Types
class EventType(Enum):
    BAR = "BAR"


@dataclass(frozen=True)
class Event:
    type: EventType
    payload: Any  # this could be a enum as well

# 3. I need a Bar, so I wrote a Bar dataclasses? 
# Why dataclass?
@dataclass(frozen=True)
class Bar:
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: datetime

# Core Data Types
class EventType(Enum):
    BAR = "BAR"
    ORDER_CREATE = "ORDER_CREATE"
    TRADE = "TRADE"


class AssetType(Enum):
    CASH = "CASH"


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "MARKET"
    STOP = "STOP"


@dataclass(frozen=True, slots=True)
class Event:
    type: EventType
    payload: Any  # this could be a enum as well


# 3. I need a Bar, so I wrote a Bar dataclasses? 
# Why dataclass?
@dataclass(frozen=True, slots=True)
class Bar:
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: datetime

@dataclass
class Asset:
    type: AssetType
    name: str


@dataclass(frozen=True, slots=True)
class Order:
    asset: Asset
    type: OrderType
    price: float  # TODO use decimal
    amount: float


@dataclass(frozen=True, slots=True)
class Trade:
    order_id: int
    amount: float
    price: float


# 1.  I create engine...
class Engine:

    def __init__(self, bus: EventBus, strategy: Strategy, feed: DataFeed, execution: Execution):
        self.bus = bus
        self.strategy = strategy
        self.feed = feed
        self.execution = execution

    def run(self):
        # subs
        bus.subscribe(EventType.BAR, self.strategy.on_bar)
        bus.subscribe(EventType.ORDER_CREATE, self.execution.on_order_create)
        self.bus.start()
        self.feed.start()
        
        while True:
            sleep(0.05)


class EventBus:

    def __init__(self, sample_freq: float=0.2):
        self.topics: Dict[EventType, List[Callable]] = defaultdict(list)   # TODO: Could be a priority queue
        self.events: List[Event] = list()
        self.sample_freq = sample_freq
        self.thread = Thread(target=self.blocking_run)
    
    def subscribe(self, event_type: EventType, callback: Callable):
        LOG.debug(f"Subscribe {event_type} with {callback}")
        self.topics[event_type].append(callback)  # TODO: could be duplicated callbacks.

    def push(self, event: Event):
        self.events.append(event)

    def blocking_run(self):
        """ blocking run """
        while True:
            while self.events:
                event = self.events.pop()
                _callables = self.topics[event.type]
                for _callable in _callables:
                    _callable(event.payload)
            
            sleep(self.sample_freq)  # sample frequency to avoid throttling the CPU.

    def start(self):
        """ Async run """
        LOG.info(f"EventBus thread starting...")
        self.thread.start()

    def stop(self):
        self.thread.join()


class DataFeed(ABC):

    @abstractmethod
    def start(self):
        ...


class DummyBarFeed(DataFeed):
    # Does Bar feed needs to know EventBus?

    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        self.thread = Thread(target=self._run)

    def start(self):
        LOG.info(f"{self} thread starting...")
        self.thread.start()

    def _run(self):
        while True:
            sleep(2)
            bar = Bar(
                open=100,
                high=200,
                low=100,
                close=100,
                volume=20000,
                timestamp=datetime.now()
            )
            event = Event(
                type=EventType.BAR,
                payload=bar
            )
            LOG.debug(f"DummyBarFeed pushed {event}")
            self.bus.push(event)


class Execution(ABC):

    @abstractmethod
    def submit_order(self, order: Order) -> int:
        ...

    @abstractmethod
    def cancel_order(self, order_id: int):
        ...

    @abstractmethod
    def modify_order(self, order_id: int, order: Order):
        ...

    @abstractmethod
    def on_order_create(self, order: Order):
        ...

    @abstractmethod
    def start(self):
        ...
    

class DummyExecution(Execution):
    
    def __init__(self, bus: EventBus) -> None:
        self.bus = bus

    def submit_order(self, order: Order) -> int:
        return super().submit_order(order)

    def cancel_order(self, order_id: int):
        return super().cancel_order(order_id)

    def modify_order(self, order_id: int, order: Order):
        return super().modify_order(order_id, order)

    def on_order_create(self, order: Order):
        LOG.info(f"Execution recieved {order =  }")
        
    def start(self):
        return super().start()


# 2. I write down strategy class
class Strategy:

    def __init__(self, bus: EventBus) -> None:
        self.bus = bus

    def on_bar(self, bar: Bar):
        latency = datetime.now() - bar.timestamp
        LOG.info(f"Strategy reveived {bar} with latency {latency.microseconds / 1000} ms")
        LOG.info(f"Computing some fancy signal ...")
        LOG.info(f"Submit Order...")
        self.submit_order()
    
    def submit_order(self):
        order = Order(
            asset=Asset(AssetType.CASH, name="Bitcoin"), 
            type=OrderType.MARKET,
            price=-1,
            amount=1.0,
        )
        event = Event(
            EventType.ORDER_CREATE,
            payload=order
        )
        self.bus.push(event)
        

        
if __name__ == "__main__":
    
    LOG.debug("Tesing EventBus")
    bus = EventBus(sample_freq=0.05)
    strat = Strategy(bus)
    execution = DummyExecution(bus)
    feed = DummyBarFeed(bus)
    engine = Engine(bus, strategy=strat, feed=feed, execution=execution)

    engine.run()