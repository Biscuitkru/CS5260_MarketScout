"""
MarketScout: Config
====================================
Just constants for now
"""
import os

ORCHESTRATOR_MODEL: str = os.getenv("ORCHESTRATOR_MODEL", "gemini-2.5-flash")
ANALYST_MODEL: str = os.getenv("ANALYST_MODEL", "gemini-2.5-flash")
PUBLISHER_MODEL: str = os.getenv("PUBLISHER_MODEL", "gemini-2.5-pro")
