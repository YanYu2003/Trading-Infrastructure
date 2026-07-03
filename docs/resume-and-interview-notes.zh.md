# 简历与面试复习笔记

本文档用于长期维护 US Equity Mini Trading Infrastructure 项目的中文复习材料。后续每完成一个新阶段、新模块、重要设计变化、面试问答或简历表达升级，都应该同步更新本文档和英文版 `docs/resume-and-interview-notes.md`。

## 项目定位

### 一句话介绍

这是一个 mock-first 的美股 Mini OMS 交易基础设施项目，目标是展示量化交易开发、Execution、OMS、自动化交易系统方向的工程能力。项目重点不是预测股价，也不是展示策略收益，而是实现行情建模、订单生命周期、风控前置校验、Broker Adapter、模拟成交、持仓/现金/PnL 更新和可测试架构。

### 这个项目不是什么

- 不是股票价格预测项目。
- 不是策略收益展示项目。
- 不是投资建议。
- MVP 阶段不做 live trading。
- 默认只使用 Mock Broker，后续最多先扩展 Paper Trading。
- 任何接近真实交易的功能都必须显式隔离和默认禁用。

### 面试开场版本

> 我在做一个 mock-first 的美股 Mini OMS 交易基础设施项目，目标是展示 Execution / OMS 方向的工程能力，而不是做策略收益预测。整体链路是：行情事件进入系统后，由策略生成交易信号，经过 pre-trade risk 检查，再由 OMS 管理订单生命周期，通过 Broker Adapter 执行，最后根据 Fill 更新持仓、现金和 PnL。目前我已经完成了工程骨架、核心领域模型和订单状态机。

## 当前项目进度

### 已完成：Phase 0

Phase 0 建立了项目基础：

- `README.md` 第一版。
- `AGENTS.md` 安全与开发规范。
- `pyproject.toml` Python 项目配置。
- `.env.example` 默认 mock 配置。
- `docs/research/open-source-comparison.md`，调研 Lean、NautilusTrader、vn.py、OpenAlgo、quanttrader、IBKR 示例和事件驱动回测思想。
- `docs/architecture.md`，记录项目架构、模块边界和 MVP 范围。
- `src/mini_trading` 最小 Python 包结构。
- smoke test，验证包可 import 且 live trading 默认关闭。

### 已完成：Phase 1

Phase 1 实现了核心交易领域模型和订单状态机：

- `Symbol`
- `Quote`
- `Trade`
- `MarketDataEvent`
- `Order`
- `Fill`
- `Position`
- `PnL`
- `AccountSnapshot`
- `OrderSide`
- `OrderType`
- `OrderStatus`
- `MarketDataEventType`
- `VALID_ORDER_TRANSITIONS`
- `can_transition`
- `assert_transition`
- `transition_order`

最近一次 Phase 1 验证结果：

```text
python -m pytest -q
17 passed
```

环境说明：项目目标版本是 Python 3.11 或 3.12，但当前本机只检测到 Python 3.10.10。Phase 1 当前逻辑使用标准库能力，在当前解释器上测试通过；正式长期开发仍建议安装 Python 3.11 并创建项目本地 `.venv`。

### 已完成：Phase 2

Phase 2 把 Phase 1 的模型串成了本地确定性的交易核心：

- `RiskEngine`
- `RiskLimits`
- `RiskCheckResult`
- `Portfolio`
- `BrokerAdapter`
- `BrokerResult`
- `MockBroker`
- `OrderManager`
- `OrderSubmissionResult`

已实现行为：

- broker 提交前执行 pre-trade risk
- kill switch 拒单
- 单笔订单金额上限拒单
- 现金不足拒单
- 最大持仓限制拒单
- long-only 模式下禁止超卖
- 重复未完成订单拒单
- market order 全额成交
- limit buy / sell 成交条件判断
- limit 条件不满足时订单保持 `SUBMITTED`
- broker 拒单不更新 portfolio
- partial fill 状态和已成交数量记录
- submitted 订单撤单且不更新 portfolio
- 基于 Fill 更新 cash 和 position
- 加权平均成本计算
- 卖出成交产生 realized PnL
- mark-to-market 计算 unrealized PnL
- account snapshot equity 计算
- buy/sell 端到端集成交易流

最近一次 Phase 2 验证结果：

```text
python -m pytest -q
42 passed
```

### 已完成：Phase 3

Phase 3 把确定性 mock 行情和简单策略接入 Phase 2 交易核心：

- `MarketDataProvider`
- `MockMarketDataProvider`
- `StrategySignal`
- `PriceThresholdStrategy`
- `TradingEngine`
- `TradingRunSummary`
- `run_demo()`

已实现行为：

- 确定性 trade event stream。
- 支持 quote event stream。
- 价格低于买入阈值时产生 buy signal。
- 买入后价格高于卖出阈值时产生 sell signal。
- 策略已有仓位时避免重复 buy signal。
- MVP 策略忽略 quote event。
- market data -> strategy -> OrderManager 的事件驱动路由。
- 完整 buy/sell 交易链路经过 RiskEngine、MockBroker、Portfolio、AccountSnapshot。
- 确定性 CLI demo summary。

最近一次 Phase 3 验证结果：

```text
python -m pytest -q
55 passed
```

未执行 editable install 时，可在项目根目录这样运行 demo：

```powershell
$env:PYTHONPATH='src'
python -m mini_trading.app.cli_demo
```

### 已完成：Phase 4

Phase 4 增加了回放报告和可导出 artifacts：

- 每个 market data event 处理后的 account snapshot。
- `ReplayReport`
- JSON report serialization。
- orders CSV。
- fills CSV。
- account snapshots CSV。
- CLI report writer。

已实现行为：

- 事件回放过程中的 mark-to-market account snapshots。
- 可检查的 report dictionary。
- 包含 final cash、equity、PnL 的 JSON summary。
- CSV order records。
- CSV fill records。
- CSV account snapshot records。
- demo report artifact writing。

最近一次 Phase 4 验证结果：

```text
python -m pytest -q
62 passed
```

生成报告的 demo 命令：

```powershell
$env:PYTHONPATH='src'
python -m mini_trading.app.cli_demo reports/demo
```

### 已完成：Phase 5A

Phase 5A 增加了 SQLite run-history 持久化：

- `SQLiteRunStore`
- `runs` 表
- `signals` 表
- `orders` 表
- `fills` 表
- `account_snapshots` 表
- `snapshot_positions` 表
- CLI `--sqlite` 输出选项

已实现行为：

- 将完成后的 `TradingRunSummary` 用一个 SQLite transaction 保存。
- 持久化策略信号、最终订单记录、成交、账户快照和逐快照持仓。
- 将 `Decimal` 金额和数量保存为精确字符串，而不是 SQLite `REAL`。
- 将 datetime 保存为 ISO-8601 字符串。
- 拒绝空白 `run_id`。
- 通过 SQLite primary key 拒绝重复 `run_id`。
- 保持交易核心边界：OMS、RiskEngine、BrokerAdapter、Strategy、Portfolio 都不依赖 SQLite。

最近一次 Phase 5A 验证结果：

```text
python -m pytest -q
70 passed
```

生成 SQLite run history 的 demo 命令：

```powershell
python -m mini_trading.app.cli_demo --sqlite reports/demo.sqlite
```

## 架构叙事

MVP 目标链路：

```text
MockMarketDataProvider
        |
        v
PriceThresholdStrategy
        |
        v
RiskEngine
        |
        v
OrderManager
        |
        v
MockBroker
        |
        v
Portfolio / Account / PnL
```

事件视角：

```text
MarketDataEvent
  -> StrategySignal
  -> RiskCheckResult
  -> Order
  -> Fill
  -> AccountSnapshot
```

### 核心边界原则

每个模块只做自己的事：

- Strategy 只生成交易意图，不直接改订单和账户。
- RiskEngine 负责订单提交前的风险检查。
- OMS 负责订单 ID、生命周期和状态一致性。
- BrokerAdapter 负责把内部订单转换成外部执行请求，并把外部回报转换成内部 Fill 和状态更新。
- Portfolio 根据 Fill 更新现金、持仓、平均成本和 PnL。

## 关键设计概念

### OrderStatus

代码位置：`src/mini_trading/core/enums.py`

`OrderStatus` 表示一笔订单当前处于哪个生命周期阶段：

- `CREATED`：订单已经在系统内部创建，但还没有提交到执行端。
- `SUBMITTED`：订单已经通过内部流程，并提交给 broker 或执行适配器。
- `PARTIALLY_FILLED`：订单只成交了一部分，还有剩余数量。
- `FILLED`：订单全部成交，属于终态。
- `CANCELLED`：订单剩余部分被取消，属于终态。注意 cancelled 不一定表示完全没有成交。
- `REJECTED`：订单被内部风控、broker 或交易所拒绝，属于终态。

面试关键点：

> 即使 market order 很快成交，OMS 内部也应该保留 `CREATED -> SUBMITTED -> FILLED`，因为 `SUBMITTED` 代表订单已经从内部交易意图进入执行端，这对日志、审计和排查很重要。

### 订单状态机

代码位置：`src/mini_trading/core/order_state.py`

当前 MVP 允许的状态流转：

```text
CREATED -> SUBMITTED
CREATED -> CANCELLED
CREATED -> REJECTED

SUBMITTED -> PARTIALLY_FILLED
SUBMITTED -> FILLED
SUBMITTED -> CANCELLED
SUBMITTED -> REJECTED

PARTIALLY_FILLED -> FILLED
PARTIALLY_FILLED -> CANCELLED
```

终态：

```text
FILLED
CANCELLED
REJECTED
```

终态不能继续流转。这样可以防止 OMS 出现不可能状态，例如 `FILLED -> SUBMITTED` 或 `CANCELLED -> FILLED`。

面试表达：

> 我用状态机集中管理订单生命周期，避免业务模块随意修改订单状态。这样可以显式限制合法流转，保护 OMS 的状态一致性，也方便后续日志审计和异常排查。

### Order 和 Fill 为什么分开

代码位置：`src/mini_trading/core/models.py`

`Order` 表示交易意图：

```text
我想买 100 股 AAPL。
```

`Fill` 表示实际成交结果：

```text
实际成交了 40 股 AAPL，价格是 180.25。
```

二者关系：

```text
1 Order -> 0 Fill
1 Order -> 1 Fill
1 Order -> many Fills
```

必须分开的原因：

- 一笔订单可能完全没有成交。
- 一笔订单可能部分成交。
- 一笔订单可能分多次、多个价格成交。
- 一笔订单可能部分成交后取消。
- 持仓、现金和 PnL 应该根据 Fill 更新，而不是根据原始 Order 更新。

面试回答：

> 我把 Order 和 Fill 分开，因为 Order 是交易意图，Fill 是实际成交。一笔订单可能没有成交，也可能有多个成交回报。账户和 PnL 的更新应该基于 Fill，因为只有真实成交才改变现金和持仓。

### RiskEngine 和 Pre-Trade Risk

代码位置：`src/mini_trading/core/risk.py`

`RiskEngine` 是订单提交前的风控门。它在订单进入 broker adapter 之前判断订单是否允许执行。

当前 MVP 风控规则：

- kill switch 开启时拒绝所有订单。
- 单笔订单 notional 上限。
- 买单现金检查。
- 买单最大持仓限制。
- long-only 模式下卖单不能超过当前持仓。
- 重复未完成订单检查。

面试回答：

> Pre-trade risk 是订单进入执行系统前的风险检查。在我的项目中，OrderManager 会先调用 RiskEngine，如果风控失败，订单直接进入 `REJECTED`，不会调用 broker，也不会更新 portfolio。这样可以把不安全或不合理订单挡在执行路径之外。

### MockBroker

代码位置：`src/mini_trading/brokers/mock.py`

`MockBroker` 用来在本地模拟执行回报，不连接真实券商。

它支持：

- market order 全额成交。
- market price 不高于 limit price 时 limit buy 成交。
- market price 不低于 limit price 时 limit sell 成交。
- limit 条件不满足时返回 submitted/no-fill。
- 确定性 partial fill。
- 确定性 broker reject。

面试回答：

> MockBroker 不是为了模拟完整市场微观结构，也不是撮合引擎。它的作用是提供可重复、可控的成交回报，让我能在没有真实资金风险和外部 API 依赖的情况下测试 OMS 状态机、部分成交、拒单和账户更新。

### OrderManager

代码位置：`src/mini_trading/core/oms.py`

`OrderManager` 负责编排 Phase 2 的交易核心：

```text
创建 Order
  -> RiskEngine.check_order
  -> CREATED 状态流转到 SUBMITTED
  -> BrokerAdapter.submit_order
  -> 更新 Order 状态和 filled quantity
  -> 根据 Fill 更新 Portfolio
```

关键不变量：

- risk 拒单不会调用 broker。
- broker 拒单不会更新 portfolio。
- limit 未成交订单保持 submitted。
- submitted 或 partially filled 订单可以通过状态机撤单。
- 只有 Fill 会改变 cash、position 和 PnL。

面试回答：

> OrderManager 是协调层。它不自己计算 PnL，也不自己模拟 broker 执行，而是把风控交给 RiskEngine，把执行交给 BrokerAdapter，把账户更新交给 Portfolio。

### Quote 和 Trade 为什么分开

`Quote` 是报价：

```text
bid = 当前买方愿意出的最高价
ask = 当前卖方愿意接受的最低价
spread = ask - bid
```

`Trade` 是实际成交：

```text
price = 成交价格
quantity = 成交数量
```

必须分开的原因：

- Quote 更新不代表发生了成交。
- Trade 发生也不一定伴随新的 Quote。
- 模拟 market buy 通常参考 ask。
- 模拟 market sell 通常参考 bid。
- 最近成交价不一定等于当前可交易报价。

面试回答：

> Quote 和 Trade 都是行情数据，但语义不同。Quote 表示当前 bid/ask 流动性，Trade 表示实际成交。分开建模可以让后续 WebSocket 行情 adapter 更自然地处理 quote channel 和 trade channel，也能支持 spread、last price、mid price 等不同用途。

### MockMarketDataProvider

代码位置：`src/mini_trading/marketdata/mock.py`

`MockMarketDataProvider` 是确定性的标准化行情事件源。它可以产生 `Trade` 和 `Quote` 事件，并且可以重复迭代，因此测试和 demo 是可复现的。

面试回答：

> 我用 MockMarketDataProvider 模拟行情流，不依赖真实 API 或 WebSocket。它产出的仍然是标准 MarketDataEvent，因此下游策略和 OMS 链路不需要知道数据到底来自 mock、CSV 还是未来的真实 WebSocket。

### StrategySignal 和 PriceThresholdStrategy

代码位置：`src/mini_trading/strategies/base.py` 和 `src/mini_trading/strategies/threshold.py`

`StrategySignal` 表示交易意图，不是订单。它包含 symbol、side、order type、quantity 和 reference price。

`PriceThresholdStrategy`：

- 监听 trade event。
- 忽略 quote event。
- 价格低于 `buy_below` 时买入。
- 买入后价格高于 `sell_above` 时卖出。
- 已有仓位时避免重复买入信号。
- 区分 signal 状态和确认成交状态。
- 通过 `on_order_result()` 根据执行结果更新确认仓位状态。

面试回答：

> 阈值策略是刻意保持简单的，它不是为了证明策略收益，而是为了产生确定性的信号，验证基础设施链路：market data -> signal -> risk -> order -> broker -> fill -> portfolio。

重要 review 结论：

> 策略信号不等于成交。策略不应该因为发出了 buy signal 就假设自己已经持仓。现在策略会等待 OrderManager 的执行反馈，再更新确认仓位状态。

### TradingEngine

代码位置：`src/mini_trading/core/engine.py`

`TradingEngine` 是 MVP 事件 runner：

```text
MarketDataEvent
  -> Strategy.on_event
  -> StrategySignal
  -> OrderManager.submit_order
  -> TradingRunSummary
```

面试回答：

> TradingEngine 在语义上是事件驱动的：它按顺序处理 market data event，并对每个事件作出反应。MVP 阶段仍然保持同步执行，是为了让测试确定、可复现。后续可以把 MarketDataProvider 换成 async WebSocket provider，而不改变 strategy、OMS、risk、broker、portfolio 的边界。

### ReplayReport

代码位置：`src/mini_trading/reports/replay.py`

`ReplayReport` 把 `TradingRunSummary` 转换成可复盘 artifacts：

- `summary.json`
- `orders.csv`
- `fills.csv`
- `account_snapshots.csv`

面试回答：

> Phase 4 让系统具备可复盘性。它不是只打印最终 PnL，而是在每个 market data event 后记录 account snapshot，并把 orders、fills、account state changes 导出成 JSON/CSV，方便解释账户如何随事件变化。

### SQLiteRunStore 和持久化边界

代码位置：`src/mini_trading/persistence/sqlite.py`

`SQLiteRunStore` 用来保存已经完成的交易 run。它接收 `TradingRunSummary`，在 `TradingEngine.run()` 完成之后，把运行结果写入 SQLite。

它持久化：

- run 级别统计和最终账户值。
- strategy signals。
- final order states。
- fills。
- account snapshots。
- 每个 snapshot 中的 positions。

关键依赖方向：

```text
TradingEngine -> TradingRunSummary -> SQLiteRunStore -> SQLite
```

依赖不反向。`core.engine`、`core.oms`、`core.risk`、`brokers`、`strategies` 和 `portfolio` 都不 import SQLite。这样交易核心逻辑不被数据库污染，测试时也不需要数据库。

金融金额保存为字符串：

```text
Decimal("100120") -> "100120"
```

原因：

- SQLite 没有原生 fixed-precision decimal 类型。
- SQLite `REAL` 是浮点数。
- 金融审计记录应该保留精确值。

面试回答：

> 我把 SQLite 设计成持久化边界，而不是交易核心的一部分。TradingEngine 在内存里计算出 TradingRunSummary，SQLiteRunStore 再用事务把这个结果记录下来。我把 Decimal 存成 text，避免浮点误差，同时保存每个账户快照里的持仓明细，让 PnL 可以按 symbol 解释。

### Position、AccountSnapshot 和 PnL

`Position` 表示单个 symbol 的持仓：

- `quantity`：当前持有数量。
- `average_cost`：平均持仓成本。
- `last_price`：最新估值价格。
- `market_value = quantity * last_price`
- `unrealized_pnl = (last_price - average_cost) * quantity`

`PnL` 分为：

- `realized`：已实现盈亏，通常来自卖出或平仓。
- `unrealized`：未实现盈亏，也就是当前持仓按最新价格估值后的账面盈亏。

`AccountSnapshot` 聚合：

- `cash`
- `positions`
- `pnl`
- `gross_market_value`
- `equity = cash + gross_market_value`

面试回答：

> Position 记录当前持有什么，PnL 解释盈亏来源，AccountSnapshot 给出某个时刻的账户整体状态。Cash 和 equity 不一样，买入股票后 cash 会减少，但 equity 包含现金和持仓市值。

Phase 2 已经实现基于 Fill 的 portfolio 更新。买入成交会减少 cash、增加 position；多次买入用加权平均法更新 average_cost；卖出成交会增加 cash、减少 position，并根据卖出价和 average_cost 计算 realized PnL。

## Python 工程取舍

### Decimal

价格、数量、成交金额、现金和 PnL 使用 `Decimal`，不用 `float`。

原因：

- `float` 是二进制浮点数，很多十进制小数无法精确表示。
- 金额和 PnL 需要稳定、可解释的计算。
- 使用 Decimal 更利于测试和对账。

成熟回答：

> Decimal 适合 MVP 阶段保证金额语义清晰和计算稳定。但在低延迟热点路径中，真实系统也可能使用 fixed-point integer，例如用 tick 或 cents 表示价格。

### Enum

`OrderSide`、`OrderType`、`OrderStatus`、`MarketDataEventType` 使用 `str, Enum`。

原因：

- 它们都是有限的领域值集合。
- 可以避免魔法字符串和拼写错误。
- 字符串枚举方便日志、JSON API 和未来数据库字段。

### dataclass

核心模型使用 `dataclass`，因为这些对象主要是有明确字段的领域对象。

相比 dict，dataclass 的好处：

- 字段明确。
- 类型更清晰。
- 测试可读性更好。
- 重构更安全。
- 可以在 `__post_init__` 集中做业务校验。

### frozen=True

核心领域对象使用 frozen dataclass。

原因：

- 避免隐藏 mutation。
- 强制订单状态变化通过状态机函数。
- 测试更容易理解。
- 为后续审计日志和事件记录打基础。

取舍：

> 不可变对象更新时要创建新实例，有一定成本。MVP 阶段更重视正确性、可测试性和审计清晰性；如果后续出现性能热点，可以局部优化。

### 为什么 core 层不用 Pydantic

Pydantic 更适合系统边界：

- API request/response
- JSON 解析
- 配置校验

当前 core domain 使用标准库 dataclass，目的是让交易核心逻辑不依赖 FastAPI 或序列化框架。未来 FastAPI 层可以用 Pydantic schema，再转换成 core dataclass。

### 为什么使用 `src/` layout

项目结构：

```text
src/mini_trading
tests
docs
```

原因：

- 源码、测试、文档分离。
- 更接近可安装 Python 包结构。
- 避免测试时意外从项目根目录导入未安装代码。

## 测试与质量保障

当前测试的重点不是追求覆盖率数字，而是保护交易系统的业务不变量。

### Smoke Test

`tests/unit/test_package_smoke.py` 验证：

- 包可以 import。
- `__version__` 存在。
- 默认交易模式是 `mock`。
- live trading 默认关闭。

面试点：

> 安全默认值不是只写在 README 里，而是有可执行测试保护。

### 核心模型测试

`tests/unit/test_core_models.py` 验证：

- symbol 标准化。
- 空 ticker 拒绝。
- quote bid/ask 必须为正。
- bid 不能高于 ask。
- quote spread。
- trade price 和 quantity 必须为正。
- trade notional。
- MarketDataEvent 能拿到 symbol。
- market order 默认是 `CREATED`。
- limit order 必须有 limit price。
- fill notional。
- position market value。
- position unrealized PnL。
- account gross market value。
- account equity。

### 状态机测试

`tests/unit/test_order_state.py` 验证：

- `CREATED` 的合法流转。
- `SUBMITTED` 的合法流转。
- `PARTIALLY_FILLED` 的合法流转。
- 终态不能继续流转。
- 非法流转抛出 `InvalidOrderTransition`。
- `transition_order` 返回新订单，不修改原订单。

### Phase 2 测试

Phase 2 新增测试覆盖：

- RiskEngine 放行与拒单路径。
- kill switch。
- 单笔金额上限。
- 现金不足。
- 最大持仓限制。
- 超卖拒绝。
- 重复未完成订单。
- Portfolio 买入/卖出成交更新。
- 加权平均成本。
- realized / unrealized PnL。
- MockBroker 全额成交、limit 未成交、partial fill 和 reject。
- OrderManager risk rejection、broker rejection、limit submitted、partial fill、full fill。
- OrderManager 对 submitted 订单的撤单。
- buy/sell 端到端集成交易流。

### Phase 3 测试

Phase 3 新增测试覆盖：

- 确定性 mock trade stream。
- quote event 包装。
- provider 可重复迭代。
- threshold buy/sell signal。
- 策略忽略 quote event。
- 已有仓位时避免重复 buy signal。
- rejected buy signal 后策略可以恢复。
- market data 到 account snapshot 的事件驱动 buy/sell 链路。
- quote-only stream 不产生交易。
- 确定性 CLI demo summary。

### Phase 4 测试

Phase 4 新增测试覆盖：

- 每个事件后的 account snapshots。
- 没有新订单时 mark-to-market equity 变化。
- report dictionary conversion。
- JSON report serialization。
- orders CSV。
- fills CSV。
- account snapshots CSV。
- CLI report artifact writing。

### Phase 5A 测试

Phase 5A 新增测试覆盖：

- SQLite schema initialization。
- run counts 和最终账户值持久化。
- strategy signals 持久化。
- final order records 持久化。
- fills 和 notional 持久化。
- account snapshots 持久化。
- 每个 snapshot 下的 position 持久化。
- `Decimal` 精确字符串存储。
- 空白 `run_id` 拒绝。
- 重复 `run_id` 拒绝。
- CLI SQLite database writing。
- 原有 JSON/CSV CLI 输出兼容。

测试类面试回答：

> 我的测试重点是保护交易系统不变量，例如订单数量必须为正、limit order 必须有 limit price、bid 不能高于 ask、fill notional 必须正确、filled/cancelled/rejected 是终态。状态机测试覆盖合法和非法流转，防止 OMS 出现不可能状态。

## 高频面试问答

### 金融与交易基础

#### ticker / symbol 是什么？

Ticker 或 symbol 是交易标的代码，例如 `AAPL`、`MSFT`。在系统里，它是行情、订单、成交和持仓之间的关联键。

#### Quote 和 Trade 有什么区别？

Quote 是报价，包含 bid 和 ask；Trade 是实际成交，包含成交价格和成交数量。Quote 不代表成交，Trade 才表示市场上真的发生了交易。

#### bid、ask、spread 是什么？

Bid 是买方愿意出的最高价，ask 是卖方愿意接受的最低价，spread 是 `ask - bid`，可以反映立即交易成本和流动性。

#### market order 和 limit order 区别是什么？

Market order 追求尽快成交，不指定价格；limit order 指定最差可接受价格。Buy limit 不应高于 limit price 成交，sell limit 不应低于 limit price 成交。

#### partial fill 是什么？

Partial fill 是部分成交。例如买 100 股，只成交了 40 股，订单状态就是 `PARTIALLY_FILLED`，剩余 60 股可能继续成交或被取消。

#### cancelled 和 rejected 有什么区别？

Cancelled 表示订单剩余部分被撤销，可能已经有部分成交；rejected 表示订单被风控、broker 或交易所拒绝，通常不应产生 fill。

#### pre-trade risk 是什么？

Pre-trade risk 是下单前风险检查，例如订单金额上限、现金检查、最大持仓、重复订单检查、kill switch。目标是在订单进入执行系统前拦截明显不安全的请求。

#### 当前 RiskEngine 如何决定是否拒单？

它先检查 kill switch，然后检查订单 notional、买单现金是否足够、买单是否超过最大持仓、卖单是否超过当前持仓，以及是否存在同 symbol 同方向的未完成重复订单。如果任一检查失败，返回 rejected 的 `RiskCheckResult`，OrderManager 会把订单标记为 `REJECTED`，且不调用 broker。

### OMS / Execution 系统设计

#### 为什么需要 OMS？

OMS 管理订单 ID、订单生命周期、状态一致性、成交回报和异常状态。它不只是一个 buy/sell 函数。

#### 为什么策略不能直接调用 broker？

策略应该只生成交易意图。直接调用 broker 会绕过风控、OMS 状态管理、日志审计和安全控制。

#### 为什么需要 BrokerAdapter？

BrokerAdapter 隔离外部券商接口差异。OMS 使用内部 `Order` 和 `Fill` 模型，adapter 负责和 Alpaca、IBKR、FIX 或 MockBroker 之间转换。

#### 为什么先做 MockBroker？

MockBroker 可以本地、确定性、安全地测试 filled、partial fill、rejected、cancelled 等场景，不依赖 API key、网络、市场时间或真实资金。

#### 现在 OrderManager 做什么？

OrderManager 创建订单、执行风控检查、把通过风控的订单提交给 broker adapter、把成交回报应用到 portfolio，并保存订单和成交历史。它是协调层，但不把所有业务逻辑都塞进自己内部。

#### 为什么适合事件驱动？

交易系统天然由事件组成：行情、信号、订单、成交、撤单、拒单、账户更新。事件驱动设计贴近真实交易流程，也方便后续接 WebSocket 和消息队列。

#### Phase 3 已经是真正的实时 WebSocket 系统了吗？

不是。Phase 3 在架构语义上是事件驱动，但使用确定性本地事件。这是刻意选择：先验证事件语义和交易链路，后续 WebSocket provider 可以实现同样的 `MarketDataProvider` 边界。

#### Phase 4 的 reporting 证明了什么？

它证明交易运行结果是可检查、可复盘的。报告记录 orders、fills 和 account snapshots，面试官可以追踪 market events 如何触发 signals、fills、cash 变化、equity 变化和 PnL。

#### 为什么使用简单的 price-threshold strategy？

因为项目重点是交易基础设施，不是 alpha research。阈值策略容易理解、容易测试，适合作为信号发生器来验证 OMS、风控、broker 和 portfolio 链路。

#### 为什么要隔离 mock / paper / live？

三者风险等级不同。Mock 是本地模拟，paper 是券商模拟环境，live 涉及真实资金。系统必须默认禁用 live trading，并隔离 endpoint、credential 和代码路径。

### Python 工程设计

#### 为什么现在不用 FastAPI？

项目核心目标是先实现 OMS 和交易闭环。FastAPI 应该作为后续薄接口层读取订单、持仓和账户状态，而不是让 HTTP endpoint 承载核心交易逻辑。

#### 为什么 Phase 5A 才引入 SQLite，而不是更早？

应该先稳定领域模型，再设计持久化 schema。如果在 `Order`、`Fill`、`AccountSnapshot`、`TradingRunSummary` 还没稳定时就设计数据库，很容易把临时实现细节固化进表结构。Phase 5A 在内存交易闭环和 replay report 稳定后引入 SQLite，因此数据库记录的是清晰的交易事实，而不是驱动核心业务逻辑。

#### 为什么用 SQLite，而不是 PostgreSQL 或 ORM？

当前目标是本地、确定性、可演示的 run history。SQLite 不需要部署服务，使用 Python 标准库即可运行，非常适合 MVP 和面试展示。PostgreSQL 或 SQLAlchemy 可以在需要多用户访问、迁移管理、更复杂查询或生产部署时再引入。

#### 为什么 Decimal 存成 text？

SQLite `REAL` 是浮点表示，不适合作为金融审计金额。项目领域模型使用 `Decimal`，持久化时保存为 `"100120"`、`"99"` 这样的字符串，可以避免浮点误差，让数据库记录和内存计算保持一致。

#### 为什么现在不用 Kafka / Redis / RabbitMQ？

应该先定义清楚事件语义，再选择传输工具。等 MarketDataEvent、OrderEvent、FillEvent、AccountSnapshot 等事件边界稳定后，再考虑 Redis Streams、RabbitMQ 或 Kafka。

#### 未来 asyncio 放在哪里？

Asyncio 应放在 I/O 边界，例如 WebSocket MarketDataProvider 和异步 BrokerAdapter。核心领域模型、状态机、PnL 计算保持同步纯逻辑，方便测试。

### 测试与可靠性

#### 如何测试状态机？

同时测试合法流转、非法流转、终态保护和不可变更新。例如 `CREATED -> FILLED` 应该被拒绝，`FILLED/CANCELLED/REJECTED` 不应继续流转。

#### 如何测试 partial fill？

构造 100 股订单，让 MockBroker 返回 40 股 fill，断言订单进入 `PARTIALLY_FILLED`，剩余 60 股，portfolio 只更新 40 股；再返回 60 股 fill，断言订单进入 `FILLED`。

Phase 2 已经实现了其中一部分：MockBroker 可以返回确定性的 partial fill，OrderManager 会记录 `PARTIALLY_FILLED`、更新 filled quantity，并且 Portfolio 只应用实际成交数量。OrderManager 也可以通过同一套状态机取消可撤订单。

#### 如何测试 rejected order？

分别测试内部 RiskEngine 拒单和外部 Broker 拒单。Rejected order 不应该产生 fill，也不应该更新 portfolio。

#### 如何测试 WebSocket 重连？

使用 fake async source 或 fake server 模拟断线和恢复，验证重试、日志、恢复后继续发出 MarketDataEvent，并避免重复处理事件。

#### 如何统计延迟？

使用 `time.perf_counter_ns()` 记录 market event handling、risk check、order processing、broker simulation、portfolio update 等阶段耗时，并输出吞吐、p50、p95、p99。

### 项目边界与扩展

#### 当前还缺什么？

当前已经完成领域模型和订单状态机，还没有实现 OrderManager、RiskEngine、MockBroker、Portfolio apply-fill 和完整交易闭环。

#### 为什么不一次性做完整系统？

交易系统模块很多，一次性做容易变成大而不稳的 demo。分阶段开发能让每个阶段都有可运行、可测试的成果，也避免过早引入 API、数据库和中间件。

#### 如何扩展到 Alpaca Paper？

新增 `AlpacaPaperBrokerAdapter`，实现和 MockBroker 一样的内部接口。把内部 Order 转成 Alpaca 请求，把 Alpaca 回报转成内部 OrderStatus 和 Fill。API key 用环境变量，endpoint 只使用 paper endpoint，live 默认禁用。

#### 如何扩展到 IBKR / FIX？

新增 adapter 处理 session、重连、外部/内部 order id 映射、execution report、reject reason 和 reconcile。核心 OMS 不依赖 IBKR 或 FIX 的协议字段。

#### 如何扩展到 C++？

Python 负责 orchestration 和业务流程，C++ 用于边界清晰的性能模块，例如 order book、matching engine、fixed-point 计算或 latency benchmark。

## 简历表达

### 当前 Phase 1 版本

中文：

> 设计美股 Mini OMS 模拟交易系统核心架构，完成 Quote/Trade/Order/Fill/Position/PnL/AccountSnapshot 等领域模型与订单状态机，基于 Decimal、Enum、不可变 dataclass 提升金额计算准确性、状态一致性和可测试性，并使用 pytest 覆盖订单非法流转、行情/成交模型校验和账户权益计算。

英文：

> Designed the core domain model and order lifecycle state machine for a mock-first US equity Mini OMS, modeling Quote, Trade, Order, Fill, Position, PnL, and AccountSnapshot with Decimal, Enum, and immutable dataclasses, with pytest coverage for invalid state transitions, market data validation, fill notional, position valuation, and account equity.

### Phase 2 已完成版本

中文：

> 基于 Python 构建 mock-first 美股 Mini OMS 模拟交易系统，实现 Market/Limit 订单、订单状态机、Pre-trade Risk、Mock Broker 成交回报、持仓/现金/PnL 更新，并通过 pytest 覆盖拒单、部分成交、撤单和账户更新等核心场景。

英文：

> Built a mock-first US equity Mini OMS in Python with market/limit orders, an order lifecycle state machine, pre-trade risk checks, mock broker execution reports, and portfolio/cash/PnL updates, with pytest coverage for rejections, partial fills, cancellations, and account state transitions.

### Phase 3 已完成版本

中文：

> 基于 Python 构建 mock-first 美股 Mini OMS 模拟交易系统，实现确定性 Mock 行情流、Price Threshold 策略信号、Pre-trade Risk、订单状态机、Mock Broker 成交回报、持仓/现金/PnL 更新，并通过 pytest 覆盖行情事件、策略信号、拒单、部分成交、撤单和端到端交易闭环。

英文：

> Built a mock-first US equity Mini OMS in Python with deterministic market data events, price-threshold strategy signals, pre-trade risk checks, order lifecycle management, mock broker execution, and portfolio/cash/PnL updates, with pytest coverage for market events, signals, rejections, partial fills, cancellations, and end-to-end trading flow.

### Phase 4 已完成版本

中文：

> 基于 Python 构建 mock-first 美股 Mini OMS 模拟交易系统，支持确定性行情回放、阈值策略信号、风控校验、Mock Broker 成交回报、持仓/现金/PnL 更新，并导出 orders、fills、account snapshots 和 summary JSON/CSV 报告，用于复盘订单生命周期、成交与账户权益变化。

英文：

> Built a mock-first US equity Mini OMS in Python with deterministic replay, threshold strategy signals, pre-trade risk checks, mock broker execution, portfolio/cash/PnL updates, and JSON/CSV reports for orders, fills, account snapshots, and final run summary.

### Phase 5A 已完成版本

中文：

> 基于 Python 构建 mock-first 美股 Mini OMS 模拟交易系统，新增 SQLite run-history 持久化层，将策略信号、订单、成交、账户快照和逐快照持仓以事务方式保存为可审计记录，并保持 OMS、风控、Broker Adapter 和 Portfolio 核心逻辑与数据库解耦。

英文：

> Built a mock-first US equity Mini OMS in Python with SQLite run-history persistence, transactionally storing strategy signals, orders, fills, account snapshots, and per-snapshot positions while keeping OMS, risk, broker, and portfolio logic independent from the database.

### 最终目标版本

中文：

> 基于 Python asyncio + WebSocket 构建美股实时行情接入模块，设计 Mini OMS 订单管理系统，实现 Market/Limit 订单、订单状态机、风控校验、成交回报、持仓与 PnL 更新；通过 Mock Broker 与可选 Alpaca Paper Trading API 完成模拟交易闭环，并针对行情处理延迟、订单处理耗时、异常重连和拒单场景进行日志监控与稳定性优化。

英文：

> Built a mock-first US equity mini trading infrastructure in Python, including market data events, a Mini OMS, order lifecycle state machine, pre-trade risk checks, mock broker execution, portfolio/cash/PnL updates, and pytest coverage for rejection, partial fills, cancellations, and account state transitions.

## 文档维护规则

后续出现以下情况时，必须同步更新中文和英文两份文档：

- 完成新的 Phase。
- 新增重要模块。
- 关键设计发生变化。
- 引入新的金融业务概念。
- 出现新的高频面试问题。
- 简历 bullet 可以升级。
- 测试或验证策略发生变化。
- 安全边界发生变化。

建议重点更新：

- 当前项目进度。
- 关键设计概念。
- 高频面试问答。
- 简历表达。
- 后续开发目标。

## 后续开发目标

### 已完成 Review：Phase 0-4 架构体检与整理

Review 文档：`docs/reviews/2026-07-03-phase-0-4-review.md`

已完成的关键整理：

- 修正策略状态同步问题，避免把 signal generation 当作 execution confirmation。
- 增加 rejected buy signal recovery 回归测试。
- 记录进入持久化阶段前的剩余工程风险。

已完成环境整理：

- 通过 `uv` 安装 Python 3.12.13。
- 创建项目本地 `.venv`。
- 初始化 git 并提交 Phase 0-4 baseline。

### 已完成 Phase 2：Mini OMS、RiskEngine、MockBroker、Portfolio

目标已完成：Phase 1 的模型已经串成本地可运行的交易核心。

计划模块：

- `src/mini_trading/core/risk.py`
- `src/mini_trading/core/oms.py`
- `src/mini_trading/core/portfolio.py`
- `src/mini_trading/brokers/base.py`
- `src/mini_trading/brokers/mock.py`

计划测试：

- `tests/unit/test_risk.py`
- `tests/unit/test_portfolio.py`
- `tests/unit/test_mock_broker.py`
- `tests/unit/test_oms.py`
- `tests/integration/test_order_execution_flow.py`

已实现行为：

- 创建 market 和 limit 订单。
- broker 提交前运行 pre-trade risk。
- 拒绝不安全订单。
- 安全订单提交到 MockBroker。
- 模拟全额成交。
- 模拟部分成交。
- 模拟 broker 拒单。
- 取消 submitted 订单。
- 更新订单 filled quantity 和状态。
- 根据 Fill 更新 cash 和 position。
- 计算 average cost。
- 计算 realized 和 unrealized PnL。
- 保持所有行为 mock-first 和 deterministic。

### 已完成 Phase 3：事件驱动交易闭环

目标已完成：mock 行情、策略、风控、OMS、broker 和 portfolio 已经串成确定性本地事件循环。

目标链路：

```text
MockMarketDataProvider
  -> PriceThresholdStrategy
  -> RiskEngine
  -> OrderManager
  -> MockBroker
  -> Portfolio
  -> AccountSnapshot
```

已实现行为：

- 确定性 mock market data stream。
- price threshold buy/sell signal。
- 完整交易闭环集成测试。
- 确定性 CLI demo summary。

### 已完成 Phase 4：回放与报告

目标已完成：交易链路可以基于确定性事件序列回放，并导出 JSON/CSV 报告。

已实现输出：

- trade records
- order records
- position changes
- account snapshots
- 简单 JSON/CSV report

### 已完成 Phase 5A：SQLite 持久化

目标已完成：完成后的交易 run 可以保存为本地 SQLite 审计记录。

已实现模块：

- `src/mini_trading/persistence/sqlite.py`
- `src/mini_trading/persistence/__init__.py`

已实现输出：

- run summary rows
- signal rows
- order rows
- fill rows
- account snapshot rows
- snapshot position rows

关键边界：

```text
TradingEngine -> TradingRunSummary -> SQLiteRunStore -> SQLite
```

数据库在交易核心完成后记录结果；它不驱动 OMS 状态流转、风控检查、broker 执行或 PnL 计算。

### 后续扩展

- FastAPI read-only 查询层。
- 更丰富的持久化查询 API。
- Alpaca Paper adapter。
- WebSocket market data provider。
- Redis/RabbitMQ/Kafka event transport。
- ClickHouse 行情或延迟分析。
- C++ 或 Rust order book / latency benchmark 性能模块。
