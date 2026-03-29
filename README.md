# MarketScout: Autonomous Market Research Agent
 
> **Project Type:** Build an AI Agent (Option 1)
 
## Overview
 
MarketScout is an autonomous market research agent that plans research strategies, navigates the web to gather data, analyzes competitors, and synthesizes findings into a professional-grade business report.
 
---
 
## I. Problem Statement
 
High-quality market research is currently gated behind expensive consultancy firms (McKinsey, BCG, etc.) or requires hundreds of hours of manual effort. Small business owners — cafe operators, boutique retailers, freelancers — often make decisions on gut feeling simply because they cannot afford actionable data.
 
No viable middle ground exists between two extremes:
 
| Option | Problem |
|---|---|
| Free Google Search | Too much noise, no structured analysis |
| $5,000+ Consultant Report | Prohibitively expensive for small businesses |
 
A small business owner who can't afford a consultant and can't spend hundreds of hours researching competitors is left without a practical way to find gaps in their local market.
 
## II. Objectives and Expected Outcome
 
MarketScout bridges the gap between free search and expensive reports by producing professional-grade due diligence and market analysis at a drastically lower cost.
 
### Expected Workflow
 
1. **Input** — A publicly accessible platform takes in a user's business idea and target location.
2. **Action** — The agent autonomously scans the competitive landscape: searching the web, identifying competitors, and analyzing customer reviews.
3. **Output** — A comprehensive report that identifies what customers dislike about local competitors and where profitable market gaps lie.
 
## III. Main Architecture
 
The solution uses an **Orchestrator–Worker architecture**. The models listed below serve as baselines and will be continually evaluated to optimize for cost and reasoning quality.
 
### The Orchestrator

The brain of the operation. Parses user intent and coordinates three specialized workers to execute the end-to-end research loop.
 
### Worker 1: The Scout
 
| | |
|---|---|
| **Role** | Searches the web for local competitors and relevant market data |
 
### Worker 2: The Analyst
 
| | |
|---|---|
| **Role** | Processes customer sentiment and reviews to pinpoint specific pain points and opportunities |
 
### Worker 3: The Publisher
 
| | |
|---|---|
| **Role** | Transforms raw JSON data from previous workers into a polished, professional report |
 
## IV. Evaluation Criteria
 
To ensure MarketScout is a reliable alternative to expensive manual research, the system will be evaluated across three core metrics:
 
**Agent Reliability:** The percentage of runs where the Orchestrator successfully completes the full research loop (scout → analyze → publish) without timing out, dropping context, or entering an infinite loop.
 
**Cost to Value:** Total token usage and API costs per generated report. The target is a comprehensive market-gap analysis produced under a strict cost threshold, proving viability for budget-constrained entrepreneurs.
 
**Output Quality:** Each successful run must deliver actionable insights beyond a basic summary: a highly structured, professional-grade market-gap report with specific, data-backed recommendations.