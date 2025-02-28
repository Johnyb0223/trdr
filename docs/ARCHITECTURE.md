# TRDR Architecture Guide

This document provides an overview of the TRDR framework's architecture and component interactions.

## Core Components

### Bar Provider

The `BarProvider` is responsible for retrieving and caching price data (OHLCV bars) for securities.

**Key Responsibilities:**
- Fetch historical price data for specified symbols
- Provide access to the most recent price data
- Cache data to minimize external API calls
- Abstract the data source implementation (Yahoo Finance, etc.)

**Implementation Classes:**
- `BaseBarProvider` (abstract class)
- `YFBarProvider` (Yahoo Finance implementation)

### Security Provider

The `SecurityProvider` transforms raw price data into rich `Security` objects that expose methods for technical analysis.

**Key Responsibilities:**
- Create and manage Security objects for each symbol
- Provide computed technical indicators (moving averages, etc.)
- Serve as an intermediary between bar data and strategy evaluation

**Implementation Classes:**
- `BaseSecurityProvider` (abstract class)
- `SecurityProvider` (concrete implementation)

### Broker

The `Broker` executes trades and manages account state information.

**Key Responsibilities:**
- Execute buy/sell orders
- Track account positions, cash, and equity
- Enforce Pattern Day Trading (PDT) rules
- Handle communication with trading API endpoints

**Implementation Classes:**
- `BaseBroker` (abstract class)
- `MockBroker` (for testing and simulation)
- `AlpacaBroker` (for live trading via Alpaca Markets)

### Strategy

The `Strategy` evaluates trading rules against market data and makes trading decisions.

**Key Responsibilities:**
- Load strategy definitions from DSL files
- Build evaluation contexts with current market data
- Evaluate entry and exit conditions
- Determine position sizing
- Execute trades through the broker

**Implementation Classes:**
- `Strategy` (handles evaluation and execution)

## Domain-Specific Language (DSL)

The TRDR DSL allows defining trading strategies in a declarative way without writing code.

**Key Components:**
- `StrategyDSLLoader`: Loads and processes `.trdr` files
- `Lexer`: Tokenizes the DSL text
- `Parser`: Builds an abstract syntax tree (AST) from tokens
- `StrategyAST`: AST representation that can be evaluated against data

## Async Design Pattern

TRDR uses the `async`/`await` pattern throughout the codebase for efficient I/O operations.

**Key Design Elements:**
- Factory methods (`create()`) initialize components asynchronously
- Components are designed to be used with the async context manager pattern
- All network and file I/O operations are implemented as coroutines

Example usage:
```python
async with await MockBroker.create(tracer=tracer) as broker:
    # Use broker within async context
    # Resources are automatically cleaned up
```

## Observability

TRDR integrates with OpenTelemetry for tracing and monitoring.

**Key Features:**
- Span-based tracing of all operations
- Detailed error reporting with exception tracking
- Performance monitoring of critical operations

## Pattern Day Trading (PDT) Rule Enforcement

TRDR enforces Pattern Day Trading regulations to prevent regulatory violations.

**Key Components:**
- `BasePDTStrategy`: Base class for PDT rule enforcement strategies
- `PDTContext`: Context object with order and account information
- `PDTDecision`: Decision object with allow/deny result and reason

**Implementation Strategies:**
- `NunStrategy`: Most restrictive (no day trading)
- `WiggleStrategy`: Allows limited day trading
- `YoloStrategy`: Most permissive (allows day trading with warnings)

## Extension Points

TRDR is designed to be extended with custom implementations:

1. **Custom Bar Providers**: Implement `BaseBarProvider` for different data sources
2. **Custom Brokers**: Implement `BaseBroker` for different trading platforms
3. **Custom PDT Strategies**: Implement `BasePDTStrategy` for different rule sets