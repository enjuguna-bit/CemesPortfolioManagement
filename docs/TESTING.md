# Testing Guide

## Running Tests

### Install Test Dependencies
```bash
pip install -r tests/requirements-test.txt
```

### Run All Tests
```bash
python run_tests.py
```

### Run Specific Test File
```bash
pytest tests/test_loan_endpoints.py -v
```

### Run Specific Test Class
```bash
pytest tests/test_loan_endpoints.py::TestDormantArrangementEndpoint -v
```

### Run with Coverage
```bash
pytest tests/ --cov=. --cov-report=html
# Open htmlcov/index.html to view coverage report
```

## Test Structure

### Integration Tests (`tests/test_loan_endpoints.py`)
- Tests all 6 loan processing endpoints
- Tests authentication and authorization
- Tests pagination and field selection
- Tests error handling
- Tests rate limiting
- Performance tests with large datasets

### Test Classes
1. **TestDormantArrangementEndpoint** - Dormant arrangement processing
2. **TestArrearsCollectedEndpoint** - Arrears collection analysis
3. **TestArrangeDuesEndpoint** - Dues arrangement
4. **TestArrangeArrearsEndpoint** - Arrears arrangement
5. **TestMTDParametersEndpoint** - MTD parameters analysis
6. **TestMTDUnpaidDuesEndpoint** - MTD unpaid dues
7. **TestProgressTracking** - Progress callback system
8. **TestErrorHandling** - Error scenarios
9. **TestRateLimiting** - Rate limit enforcement
10. **TestPerformance** - Performance benchmarks

## Progress Callbacks

### Server-Side Usage
```python
from utils.progress import create_progress_tracker
from utils.progress_processors import create_progress_processor

# Create progress tracker
operation_id = str(uuid.uuid4())
tracker = create_progress_tracker(operation_id, total_steps=100)

# Create progress-aware processor
processor = create_progress_processor('dormant', tracker)

# Process with progress updates
result = processor.process_with_progress(file_data, branch_name='Branch A')
```

### API Endpoint for Progress
```python
@app.route('/api/v1/loans/progress/<operation_id>', methods=['GET'])
@require_auth()
def get_processing_progress(operation_id):
    from utils.progress import get_progress_status
    
    status = get_progress_status(operation_id)
    if not status:
        return jsonify({'error': 'Operation not found'}), 404
    
    return jsonify(status)
```

### Android Client Integration
```kotlin
// Kotlin Coroutines + Flow
class LoanProgressTracker(private val api: ApiService) {
    
    fun trackProgress(operationId: String): Flow<ProgressUpdate> = flow {
        while (true) {
            val progress = api.getProgress(operationId)
            
            emit(ProgressUpdate(
                percentage = progress.percentage,
                message = progress.message,
                completed = progress.completed,
                metadata = progress.metadata
            ))
            
            if (progress.completed || progress.error) break
            
            delay(1000) // Poll every second
        }
    }.flowOn(Dispatchers.IO)
}

// In ViewModel
viewModelScope.launch {
    loanProgressTracker.trackProgress(operationId)
        .collect { update ->
            _progressState.value = update
        }
}

// In Compose UI
@Composable
fun LoanProcessingScreen(viewModel: LoanViewModel) {
    val progress by viewModel.progressState.collectAsState()
    
    Column {
        LinearProgressIndicator(
            progress = progress.percentage / 100f,
            modifier = Modifier.fillMaxWidth()
        )
        
        Text(text = "${progress.percentage}%")
        Text(text = progress.message)
        
        if (progress.completed) {
            Text("Processing completed!")
        }
    }
}
```

## Test Coverage Goals

- **Unit Tests**: 80%+ coverage
- **Integration Tests**: All endpoints tested
- **Error Scenarios**: All error paths covered
- **Performance**: Response time < 5s for typical requests

## Continuous Integration

Add to `.github/workflows/tests.yml`:
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r tests/requirements-test.txt
    
    - name: Run tests
      run: python run_tests.py
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```
