# 事件驱动系统化交易框架

In ONE file...

This is mainly a educational implementation. The goal is to explain the core 
concepts of event-driven trading system as clear as possible.

But with few more refactor and implementation of the interface, this is a working
framework to do backtesting and live trading.

![Architecture](./assets/fig1.png)

## V1

100 行代码 + 1 张图，理解系统化交易事件驱动框架。

量化交易开源社区绝大部分框架都是采用了事件驱动设计模式，比如：

- vnpy
- backtrader

主要的组成部分：

- Engine *
- EventBus *
- DataFeed *
- Strategy *
- Execution
- Portfolio
- Risk
- Other

[>> 视频讲解 v1](https://www.youtube.com/watch?v=wm7QLlzgo2M&t=1s)