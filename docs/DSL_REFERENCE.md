# TRDR Strategy DSL Reference

This document provides a reference for the TRDR domain-specific language (DSL) used to define trading strategies.

## Overview

The TRDR DSL is a declarative language that allows you to define trading strategies without writing code. Strategies are defined in `.trdr` files with a simple, indentation-based syntax that specifies:

- Strategy metadata (name, description)
- Entry conditions (when to buy)
- Exit conditions (when to sell)
- Position sizing rules (how much to buy)

## Basic Structure

A strategy file follows this structure:

```
STRATEGY
    NAME "Strategy Name"
    DESCRIPTION "Strategy Description"
    ENTRY
        <entry conditions>
    EXIT
        <exit conditions>
    SIZING
        <sizing rules>
```

## Conditions

Conditions can be combined using `ALL_OF` (logical AND) and `ANY_OF` (logical OR):

```
ALL_OF
    MA5 > MA20
    CURRENT_PRICE > 100
    CURRENT_VOLUME > 1000
```

```
ANY_OF
    CURRENT_PRICE > (AVERAGE_COST * 1.10)  # 10% profit
    CURRENT_PRICE < (AVERAGE_COST * 0.95)  # 5% stop loss
```

## Available Context Variables

### Price and Volume

| Variable | Description |
|----------|-------------|
| `CURRENT_PRICE` | Current price of the security |
| `CURRENT_VOLUME` | Current trading volume of the security |
| `AVERAGE_COST` | Average cost basis for current position (only in EXIT) |

### Moving Averages

| Variable | Description |
|----------|-------------|
| `MA5` | 5-day simple moving average of price |
| `MA20` | 20-day simple moving average of price |
| `MA50` | 50-day simple moving average of price |
| `MA100` | 100-day simple moving average of price |
| `MA200` | 200-day simple moving average of price |

### Volume Averages

| Variable | Description |
|----------|-------------|
| `AV5` | 5-day average volume |
| `AV20` | 20-day average volume |
| `AV50` | 50-day average volume |
| `AV100` | 100-day average volume |
| `AV200` | 200-day average volume |

### Account Information

| Variable | Description |
|----------|-------------|
| `AVAILABLE_CASH` | Available cash in the account |
| `ACCOUNT_EXPOSURE` | Current account exposure (invested/total equity) |
| `OPEN_POSITIONS` | Number of currently open positions |

## Operators

### Comparison Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `>` | Greater than | `MA5 > MA20` |
| `<` | Less than | `CURRENT_PRICE < 100` |
| `==` | Equal to | `OPEN_POSITIONS == 0` |

### Arithmetic Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `+` | Addition | `CURRENT_PRICE + 10` |
| `-` | Subtraction | `CURRENT_PRICE - 5` |
| `*` | Multiplication | `AVERAGE_COST * 1.10` |
| `/` | Division | `AVAILABLE_CASH / 4` |

### Technical Indicators

| Operator | Description | Example |
|----------|-------------|---------|
| `CROSSED_ABOVE` | A crossed above B recently | `MA5 CROSSED_ABOVE MA20` |
| `CROSSED_BELOW` | A crossed below B recently | `MA20 CROSSED_BELOW MA50` |

## Sizing Rules

Sizing rules define how much to invest when an entry condition is met. Each rule has a condition and a dollar amount:

```
SIZING
    RULE
        CONDITION
            AVAILABLE_CASH > 10000
        DOLLAR_AMOUNT 
            2000
    RULE
        CONDITION
            ACCOUNT_EXPOSURE < 0.5
        DOLLAR_AMOUNT 
            (AVAILABLE_CASH * 0.20)
```

The first rule that matches is used to determine position size.

## Complete Example

```
STRATEGY
    NAME "Moving Average Crossover Strategy"
    DESCRIPTION "Buy when MA5 crosses above MA20 with confirmation"
    
    ENTRY
        ALL_OF
            MA5 CROSSED_ABOVE MA20
            MA20 > MA50
            CURRENT_PRICE > 100
            CURRENT_VOLUME > AV20
    
    EXIT
        ANY_OF
            CURRENT_PRICE > (AVERAGE_COST * 1.08)  # 8% profit
            CURRENT_PRICE < (AVERAGE_COST * 0.96)  # 4% stop loss
            MA5 CROSSED_BELOW MA20
    
    SIZING
        RULE
            CONDITION
                AVAILABLE_CASH > 10000
            DOLLAR_AMOUNT 
                2000
        RULE
            CONDITION
                ALL_OF
                    ACCOUNT_EXPOSURE < 0.5
                    OPEN_POSITIONS < 3
            DOLLAR_AMOUNT 
                (AVAILABLE_CASH * 0.20)
        RULE
            CONDITION
                ANY_OF
                    CURRENT_PRICE < 50
                    CURRENT_VOLUME > (AV20 * 2)
            DOLLAR_AMOUNT 
                1000
```

## Best Practices

1. **Always use parentheses** for complex arithmetic expressions to ensure correct evaluation order
2. **Start with simple conditions** and test them thoroughly before adding complexity
3. **Use meaningful sizing rules** that consider your account size and risk tolerance
4. **Test with historical data** before deploying a strategy with real money
5. **Add clear comments** to document your strategy's logic and reasoning