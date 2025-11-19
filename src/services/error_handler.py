"""Enhanced Error Handling Module for AI Study Coach Agents"""
import logging
import traceback
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification"""
    API_ERROR = "api_error"
    DATABASE_ERROR = "database_error"
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    NETWORK_ERROR = "network_error"
    PROCESSING_ERROR = "processing_error"
    UNKNOWN_ERROR = "unknown_error"


class StudyCoachError(Exception):
    """Base exception class for Study Coach errors"""
    def __init__(self, message: str, category: ErrorCategory, severity: ErrorSeverity, context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context or {}
        self.timestamp = datetime.utcnow().isoformat()
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "context": self.context,
            "timestamp": self.timestamp
        }


class ErrorHandler:
    """Centralized error handling and logging"""
    
    def __init__(self, log_file: str = "study_coach_errors.log"):
        self.logger = self._setup_logger(log_file)
        self.error_count = 0
        self.critical_errors = []
    
    def _setup_logger(self, log_file: str) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("StudyCoachErrorHandler")
        logger.setLevel(logging.DEBUG)
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.ERROR)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def handle_error(self, error: Exception, category: ErrorCategory, severity: ErrorSeverity, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle and log errors with context"""
        self.error_count += 1
        
        if isinstance(error, StudyCoachError):
            error_data = error.to_dict()
        else:
            error_data = {
                "message": str(error),
                "category": category.value,
                "severity": severity.value,
                "context": context or {},
                "timestamp": datetime.utcnow().isoformat(),
                "traceback": traceback.format_exc()
            }
        
        # Log based on severity
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"Critical Error: {error_data}")
            self.critical_errors.append(error_data)
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(f"High Severity Error: {error_data}")
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"Medium Severity Error: {error_data}")
        else:
            self.logger.info(f"Low Severity Error: {error_data}")
        
        return error_data
    
    def handle_api_error(self, error: Exception, api_name: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle API-specific errors"""
        enriched_context = context or {}
        enriched_context["api_name"] = api_name
        return self.handle_error(error, ErrorCategory.API_ERROR, ErrorSeverity.HIGH, enriched_context)
    
    def handle_database_error(self, error: Exception, operation: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle database errors"""
        enriched_context = context or {}
        enriched_context["operation"] = operation
        return self.handle_error(error, ErrorCategory.DATABASE_ERROR, ErrorSeverity.HIGH, enriched_context)
    
    def handle_validation_error(self, message: str, field: str, value: Any) -> Dict[str, Any]:
        """Handle validation errors"""
        context = {"field": field, "value": str(value)}
        error = StudyCoachError(message, ErrorCategory.VALIDATION_ERROR, ErrorSeverity.MEDIUM, context)
        return self.handle_error(error, ErrorCategory.VALIDATION_ERROR, ErrorSeverity.MEDIUM, context)
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            "total_errors": self.error_count,
            "critical_errors_count": len(self.critical_errors),
            "recent_critical_errors": self.critical_errors[-5:] if self.critical_errors else []
        }


# Global error handler instance
error_handler = ErrorHandler()
