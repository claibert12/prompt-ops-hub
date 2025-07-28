"""
Integrity Core - Reusable integrity gates for Prompt Ops Hub.

This package provides all the integrity checking functionality:
- Coverage gates (global and diff)
- Trivial test detection
- Tamper checks
- Policy enforcement
- Observer pattern
"""

from .coverage import CoverageChecker
from .diff_coverage import DiffCoverageChecker
from .trivial_tests import TrivialTestChecker
from .tamper import TamperChecker
from .policy import PolicyChecker
from .observer import Observer
from .config import IntegrityConfig

__version__ = "1.0.0"
__all__ = [
    "CoverageChecker",
    "DiffCoverageChecker", 
    "TrivialTestChecker",
    "TamperChecker",
    "PolicyChecker",
    "Observer",
    "IntegrityConfig"
] 