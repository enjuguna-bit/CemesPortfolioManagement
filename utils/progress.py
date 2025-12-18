"""
Progress callback system for long-running operations
Allows Android clients to track processing progress in real-time
"""
from typing import Callable, Optional, Dict, Any
from datetime import datetime
import threading
import time


class ProgressTracker:
    """Thread-safe progress tracking for long-running operations"""
    
    def __init__(self, total_steps: int = 100, callback: Optional[Callable] = None):
        """
        Initialize progress tracker
        
        Args:
            total_steps: Total number of steps (default 100 for percentage)
            callback: Optional callback function(current, total, message, metadata)
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.callback = callback
        self.message = ""
        self.metadata = {}
        self.start_time = datetime.now()
        self._lock = threading.Lock()
        self._cancelled = False
    
    def update(self, step: int, message: str = "", **metadata):
        """
        Update progress
        
        Args:
            step: Current step number
            message: Progress message
            **metadata: Additional metadata (e.g., records_processed, file_size)
        """
        with self._lock:
            if self._cancelled:
                raise ProgressCancelled("Operation was cancelled")
            
            self.current_step = min(step, self.total_steps)
            self.message = message
            self.metadata = metadata
            
            if self.callback:
                self.callback(
                    current=self.current_step,
                    total=self.total_steps,
                    message=message,
                    metadata=metadata,
                    percentage=self.get_percentage(),
                    elapsed_seconds=self.get_elapsed_seconds()
                )
    
    def increment(self, steps: int = 1, message: str = "", **metadata):
        """Increment progress by specified steps"""
        self.update(self.current_step + steps, message, **metadata)
    
    def get_percentage(self) -> float:
        """Get current progress as percentage"""
        if self.total_steps == 0:
            return 0.0
        return round((self.current_step / self.total_steps) * 100, 2)
    
    def get_elapsed_seconds(self) -> float:
        """Get elapsed time in seconds"""
        return (datetime.now() - self.start_time).total_seconds()
    
    def cancel(self):
        """Cancel the operation"""
        with self._lock:
            self._cancelled = True
    
    def is_cancelled(self) -> bool:
        """Check if operation was cancelled"""
        with self._lock:
            return self._cancelled
    
    def complete(self, message: str = "Completed"):
        """Mark operation as complete"""
        self.update(self.total_steps, message, completed=True)


class ProgressCancelled(Exception):
    """Raised when operation is cancelled"""
    pass


# Global progress storage for tracking multiple operations
_progress_store: Dict[str, ProgressTracker] = {}
_store_lock = threading.Lock()


def create_progress_tracker(operation_id: str, total_steps: int = 100, 
                           callback: Optional[Callable] = None) -> ProgressTracker:
    """
    Create and register a progress tracker
    
    Args:
        operation_id: Unique identifier for this operation
        total_steps: Total number of steps
        callback: Optional callback function
    
    Returns:
        ProgressTracker instance
    """
    with _store_lock:
        tracker = ProgressTracker(total_steps, callback)
        _progress_store[operation_id] = tracker
        return tracker


def get_progress_tracker(operation_id: str) -> Optional[ProgressTracker]:
    """Get progress tracker by operation ID"""
    with _store_lock:
        return _progress_store.get(operation_id)


def remove_progress_tracker(operation_id: str):
    """Remove progress tracker after completion"""
    with _store_lock:
        _progress_store.pop(operation_id, None)


def get_progress_status(operation_id: str) -> Optional[Dict[str, Any]]:
    """
    Get current progress status as dictionary (for API responses)
    
    Returns:
        Dictionary with progress information or None if not found
    """
    tracker = get_progress_tracker(operation_id)
    if not tracker:
        return None
    
    return {
        'operation_id': operation_id,
        'current_step': tracker.current_step,
        'total_steps': tracker.total_steps,
        'percentage': tracker.get_percentage(),
        'message': tracker.message,
        'metadata': tracker.metadata,
        'elapsed_seconds': tracker.get_elapsed_seconds(),
        'completed': tracker.current_step >= tracker.total_steps
    }


# Example usage for Android integration
"""
# Server-side (Flask endpoint)
from utils.progress import create_progress_tracker, get_progress_status

@app.route('/api/v1/loans/process', methods=['POST'])
def process_loans():
    operation_id = str(uuid.uuid4())
    
    # Create progress tracker
    tracker = create_progress_tracker(operation_id, total_steps=100)
    
    # Start background processing
    thread = threading.Thread(
        target=process_loans_background,
        args=(file_data, tracker)
    )
    thread.start()
    
    return jsonify({
        'operation_id': operation_id,
        'status': 'processing'
    })

@app.route('/api/v1/loans/progress/<operation_id>', methods=['GET'])
def get_loan_progress(operation_id):
    status = get_progress_status(operation_id)
    if not status:
        return jsonify({'error': 'Operation not found'}), 404
    return jsonify(status)

def process_loans_background(file_data, tracker: ProgressTracker):
    try:
        tracker.update(10, "Loading data...")
        df = load_data(file_data)
        
        tracker.update(30, "Processing records...")
        results = process_records(df)
        
        tracker.update(70, "Generating report...")
        report = generate_report(results)
        
        tracker.update(90, "Saving results...")
        save_results(report)
        
        tracker.complete("Processing completed successfully")
    except Exception as e:
        tracker.update(tracker.current_step, f"Error: {str(e)}", error=True)

# Android client (Kotlin)
class LoanProcessor(private val api: ApiService) {
    
    suspend fun processLoans(file: File): Flow<ProgressState> = flow {
        // Start processing
        val response = api.startLoanProcessing(file)
        val operationId = response.operationId
        
        // Poll for progress
        while (true) {
            val progress = api.getProgress(operationId)
            
            emit(ProgressState(
                percentage = progress.percentage,
                message = progress.message,
                completed = progress.completed
            ))
            
            if (progress.completed) break
            
            delay(1000) // Poll every second
        }
    }
}

// In Activity/Fragment
lifecycleScope.launch {
    loanProcessor.processLoans(selectedFile)
        .collect { progress ->
            // Update UI
            progressBar.progress = progress.percentage.toInt()
            statusText.text = progress.message
            
            if (progress.completed) {
                // Show success
            }
        }
}
"""
