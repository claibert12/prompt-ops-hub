"""
Observer pattern for monitoring integrity checks.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from .config import IntegrityConfig


class Observer:
    """Observer for monitoring integrity checks."""
    
    def __init__(self, config: Optional[IntegrityConfig] = None):
        """Initialize observer.
        
        Args:
            config: Configuration for observer
        """
        self.config = config or IntegrityConfig()
        self.logger = self._setup_logger()
        self.events = []
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for observer.
        
        Returns:
            Configured logger
        """
        logger = logging.getLogger("integrity_observer")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # File handler if configured
            if self.config.observer_log_file:
                file_handler = logging.FileHandler(self.config.observer_log_file)
                file_handler.setLevel(logging.INFO)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
        
        return logger
    
    def log_event(self, event_type: str, data: Dict[str, Any], success: bool):
        """Log an integrity check event.
        
        Args:
            event_type: Type of event (e.g., 'coverage_check', 'tamper_check')
            data: Event data
            success: Whether the check passed
        """
        if not self.config.observer_enabled:
            return
        
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "success": success,
            "data": data
        }
        
        self.events.append(event)
        
        level = logging.INFO if success else logging.WARNING
        self.logger.log(level, f"{event_type}: {'PASS' if success else 'FAIL'}")
        
        if not success and "violations" in data:
            for violation in data["violations"]:
                self.logger.warning(f"  Violation: {violation}")
    
    def log_coverage_check(self, coverage_data: Dict[str, float], violations: List[str]):
        """Log coverage check results.
        
        Args:
            coverage_data: Coverage data
            violations: List of violations
        """
        success = len(violations) == 0
        data = {
            "coverage": coverage_data,
            "violations": violations
        }
        self.log_event("coverage_check", data, success)
    
    def log_diff_coverage_check(self, diff_files: List[str], coverage_data: Dict[str, Any], violations: List[str]):
        """Log diff coverage check results.
        
        Args:
            diff_files: List of changed files
            coverage_data: Coverage data
            violations: List of violations
        """
        success = len(violations) == 0
        data = {
            "diff_files": diff_files,
            "coverage": coverage_data,
            "violations": violations
        }
        self.log_event("diff_coverage_check", data, success)
    
    def log_trivial_test_check(self, test_files: List[str], trivial_tests: List[str], violations: List[str]):
        """Log trivial test check results.
        
        Args:
            test_files: List of test files checked
            trivial_tests: List of trivial tests found
            violations: List of violations
        """
        success = len(violations) == 0
        data = {
            "test_files": test_files,
            "trivial_tests": trivial_tests,
            "violations": violations
        }
        self.log_event("trivial_test_check", data, success)
    
    def log_tamper_check(self, changed_files: List[str], test_files: List[str], violations: List[str]):
        """Log tamper check results.
        
        Args:
            changed_files: List of changed files
            test_files: List of test/config files
            violations: List of violations
        """
        success = len(violations) == 0
        data = {
            "changed_files": changed_files,
            "test_files": test_files,
            "violations": violations
        }
        self.log_event("tamper_check", data, success)
    
    def log_policy_check(self, context: Dict[str, Any], violations: List[str]):
        """Log policy check results.
        
        Args:
            context: Policy check context
            violations: List of violations
        """
        success = len(violations) == 0
        data = {
            "context": context,
            "violations": violations
        }
        self.log_event("policy_check", data, success)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all events.
        
        Returns:
            Summary of events
        """
        if not self.events:
            return {"total_events": 0}
        
        total_events = len(self.events)
        successful_events = sum(1 for event in self.events if event["success"])
        failed_events = total_events - successful_events
        
        event_types = {}
        for event in self.events:
            event_type = event["event_type"]
            if event_type not in event_types:
                event_types[event_type] = {"total": 0, "success": 0, "failed": 0}
            event_types[event_type]["total"] += 1
            if event["success"]:
                event_types[event_type]["success"] += 1
            else:
                event_types[event_type]["failed"] += 1
        
        return {
            "total_events": total_events,
            "successful_events": successful_events,
            "failed_events": failed_events,
            "success_rate": successful_events / total_events if total_events > 0 else 0,
            "event_types": event_types,
            "last_event": self.events[-1] if self.events else None
        }
    
    def export_events(self, file_path: str):
        """Export events to JSON file.
        
        Args:
            file_path: Path to export file
        """
        with open(file_path, 'w') as f:
            json.dump(self.events, f, indent=2)
    
    def clear_events(self):
        """Clear all events."""
        self.events.clear()
    
    def calculate_integrity_score(self) -> float:
        """Calculate overall integrity score based on recent events.
        
        Returns:
            Integrity score from 0-100
        """
        if not self.events:
            return 100.0  # Default to perfect score if no events
        
        # Calculate score based on recent events (last 10)
        recent_events = self.events[-10:]
        successful_events = sum(1 for event in recent_events if event.get('success', False))
        total_events = len(recent_events)
        
        if total_events == 0:
            return 100.0
        
        # Base score on success rate
        success_rate = successful_events / total_events
        base_score = success_rate * 100
        
        # Penalize for violations
        violation_penalty = 0
        for event in recent_events:
            if not event.get('success', False):
                data = event.get('data', {})
                violations = data.get('violations', [])
                violation_penalty += len(violations) * 5  # 5 points per violation
        
        final_score = max(0, base_score - violation_penalty)
        return min(100, final_score) 