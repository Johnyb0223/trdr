# TRDR Examples

This directory contains examples demonstrating how to use the TRDR trading framework in different scenarios.

## Examples

### No Telemetry

The `no_telemetry` directory demonstrates how to use TRDR without OpenTelemetry integration. This is a simpler setup that doesn't require any tracing infrastructure.

**Key features:**
- Basic usage with MockBroker
- No telemetry/tracing configuration
- Yahoo Finance bar provider for historical data

### With Telemetry

The `with_telemetry` directory shows how to set up TRDR with OpenTelemetry for distributed tracing and monitoring.

**Key features:**
- OpenTelemetry integration with OTLP exporter
- MockBroker integration with telemetry
- Yahoo Finance bar provider for historical data
- Pattern Day Trading (PDT) strategy integration

## Strategy Examples

The `strategies` directory contains example strategy files in TRDR's domain-specific language (DSL).
