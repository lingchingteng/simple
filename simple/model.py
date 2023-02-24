from typing import Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


# Basic Data Types
class EventType(Enum):
    BAR = "BAR"
    ORDER_CREATE = "ORDER_CREATE"
    TRADE = "TRADE"


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


class AssetType(Enum):
    CASH = "CASH"


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "MARKET"
    STOP = "STOP"


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
