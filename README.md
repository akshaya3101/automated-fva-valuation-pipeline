# Automated FVA Valuation Pipeline

An end-to-end Python pipeline for valuing an internal derivatives portfolio using market data from an NSE NIFTY option-chain snapshot.

The pipeline performs market-data ingestion, normalization, validation, transformation, synthetic position generation, market matching, position-level valuation, valuation adjustments, funding valuation adjustment (FVA), and portfolio-level reporting.

---

## 1. Project Overview

This project demonstrates an automated valuation workflow for an internal options portfolio.

The pipeline takes a raw NSE NIFTY option-chain snapshot and transforms it into a structured market-data dataset. Hypothetical internal option positions are then matched against available market observations and valued using the corresponding market prices.

The valuation is subsequently adjusted for:

- Bid-ask spread
- Liquidity
- Economic consistency
- Funding costs / FVA

The final stage produces portfolio-level reconciliation and an exception report for positions requiring attention.

---

## 2. Business Objective

The objective is to demonstrate how a derivatives valuation workflow can be automated from raw market data through final portfolio reporting.

The pipeline is designed around the following valuation flow:

```text
Raw NSE Option Chain
        |
        v
     Ingestion
        |
        v
    Validation
        |
        v
   Transformation
        |
        v
Synthetic Positions
        |
        v
  Market Matching
        |
        v
Position Valuation
        |
        v
Valuation Adjustments
        |
        v
    Funding / FVA
        |
        v
Portfolio Reporting
        |
        v
    Exceptions