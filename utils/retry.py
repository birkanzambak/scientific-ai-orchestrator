"""
Retry utilities for the Scientific AI Orchestrator
-------------------------------------------------

Provides robust retry logic with exponential backoff, circuit breaker patterns,
and comprehensive error handling for the AI pipeline.
"""

import time
import logging
from functools import wraps
from typing import Callable, Any, Optional, Type, Union, List
from tenacity import (
    retry, stop_after_attempt, wait_exponential, retry_if_exception_type,
    before_sleep_log, after_log
)

logger = logging.getLogger(__name__)

class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class AgentError(PipelineError):
    """Exception raised when an agent fails."""
    def __init__(self, agent_name: str, error: Exception, context: str = ""):
        self.agent_name = agent_name
        self.original_error = error
        self.context = context
        super().__init__(f"{agent_name} failed: {error} {context}")

class RetryableError(PipelineError):
    """Exception that should trigger a retry."""
    pass

class NonRetryableError(PipelineError):
    """Exception that should not trigger a retry."""
    pass

def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: Optional[List[Type[Exception]]] = None,
    non_retryable_exceptions: Optional[List[Type[Exception]]] = None
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Parameters
    ----------
    max_attempts : int
        Maximum number of retry attempts
    base_delay : float
        Base delay between retries in seconds
    max_delay : float
        Maximum delay between retries in seconds
    retryable_exceptions : List[Type[Exception]]
        Exceptions that should trigger a retry
    non_retryable_exceptions : List[Type[Exception]]
        Exceptions that should not trigger a retry
    """
    if retryable_exceptions is None:
        retryable_exceptions = [RetryableError, ConnectionError, TimeoutError]
    
    if non_retryable_exceptions is None:
        non_retryable_exceptions = [NonRetryableError, ValueError, TypeError]
    
    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=base_delay, max=max_delay),
            retry=retry_if_exception_type(tuple(retryable_exceptions)),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.INFO)
        )
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except tuple(non_retryable_exceptions) as e:
                logger.error(f"Non-retryable error in {func.__name__}: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                raise RetryableError(f"Unexpected error: {e}") from e
        
        return wrapper
    return decorator

def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: Type[Exception] = Exception
):
    """
    Circuit breaker pattern decorator.
    
    Parameters
    ----------
    failure_threshold : int
        Number of failures before opening the circuit
    recovery_timeout : float
        Time to wait before attempting to close the circuit
    expected_exception : Type[Exception]
        Exception type to monitor for failures
    """
    def decorator(func: Callable) -> Callable:
        failures = 0
        last_failure_time = 0
        circuit_open = False
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal failures, last_failure_time, circuit_open
            
            # Check if circuit is open
            if circuit_open:
                if time.time() - last_failure_time > recovery_timeout:
                    logger.info(f"Circuit breaker for {func.__name__} attempting to close")
                    circuit_open = False
                    failures = 0
                else:
                    raise NonRetryableError(f"Circuit breaker open for {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                # Reset failure count on success
                failures = 0
                return result
            except expected_exception as e:
                failures += 1
                last_failure_time = time.time()
                
                if failures >= failure_threshold:
                    circuit_open = True
                    logger.error(f"Circuit breaker opened for {func.__name__} after {failures} failures")
                
                raise
        
        return wrapper
    return decorator

def safe_execute(
    func: Callable,
    *args,
    default_return: Any = None,
    log_errors: bool = True,
    **kwargs
) -> Any:
    """
    Safely execute a function with comprehensive error handling.
    
    Parameters
    ----------
    func : Callable
        Function to execute
    *args
        Positional arguments for the function
    default_return : Any
        Value to return if the function fails
    log_errors : bool
        Whether to log errors
    **kwargs
        Keyword arguments for the function
    
    Returns
    -------
    Any
        Function result or default_return if function fails
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger.error(f"Error executing {func.__name__}: {e}")
        return default_return

def timeout_handler(timeout_seconds: float = 30.0):
    """
    Decorator to add timeout handling to functions.
    
    Parameters
    ----------
    timeout_seconds : float
        Timeout in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import signal
            
            def timeout_handler_signal(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds} seconds")
            
            # Set up signal handler for timeout
            old_handler = signal.signal(signal.SIGALRM, timeout_handler_signal)
            signal.alarm(int(timeout_seconds))
            
            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # Cancel the alarm
                return result
            finally:
                signal.signal(signal.SIGALRM, old_handler)
        
        return wrapper
    return decorator

class PipelineMonitor:
    """Monitor for tracking pipeline performance and errors."""
    
    def __init__(self):
        self.stats = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'agent_errors': {},
            'average_response_time': 0.0,
            'total_response_time': 0.0
        }
    
    def record_run(self, success: bool, response_time: float, agent_errors: Optional[List[str]] = None):
        """Record a pipeline run."""
        self.stats['total_runs'] += 1
        self.stats['total_response_time'] += response_time
        
        if success:
            self.stats['successful_runs'] += 1
        else:
            self.stats['failed_runs'] += 1
        
        if agent_errors:
            for error in agent_errors:
                self.stats['agent_errors'][error] = self.stats['agent_errors'].get(error, 0) + 1
        
        # Update average response time
        self.stats['average_response_time'] = (
            self.stats['total_response_time'] / self.stats['total_runs']
        )
    
    def get_success_rate(self) -> float:
        """Get the success rate as a percentage."""
        if self.stats['total_runs'] == 0:
            return 0.0
        return (self.stats['successful_runs'] / self.stats['total_runs']) * 100
    
    def get_report(self) -> dict:
        """Get a comprehensive report of pipeline performance."""
        return {
            **self.stats,
            'success_rate': self.get_success_rate(),
            'failure_rate': 100 - self.get_success_rate()
        } 