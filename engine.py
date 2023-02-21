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


# 1.  I create engine...
class Engine:

    def __init__(self, bus: EventBus, strategy: Strategy, feed: DataFeed):
        self.bus = bus
        self.strategy = strategy
        self.feed = feed

    def run(self):
        # subs
        bus.subscribe(EventType.BAR, self.strategy.on_bar)
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


# 2. I write down strategy class
class Strategy:

    def on_bar(self, bar: Bar):
        latency = datetime.now() - bar.timestamp
        LOG.info(f"Strategy reveived {bar} with latency {latency.microseconds / 1000} ms")
        LOG.info(f"Computing some fancy signal ...")

        

if __name__ == "__main__":
    
    LOG.debug("Tesing EventBus")
    bus = EventBus(sample_freq=0.05)
    strat = Strategy()
    feed = DummyBarFeed(bus)
    engine = Engine(bus, strategy=strat, feed=feed)

    engine.run()