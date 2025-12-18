"""
Example of integrating progress callbacks into loan processors
"""
from utils.progress import ProgressTracker, ProgressCancelled
from typing import Optional, Dict, Any
import pandas as pd


class ProgressAwareLoanProcessor:
    """Base class for loan processors with progress tracking"""
    
    def __init__(self, progress_tracker: Optional[ProgressTracker] = None):
        self.progress = progress_tracker or ProgressTracker(100)
    
    def process_with_progress(self, file_input, **kwargs) -> Dict[str, Any]:
        """
        Process loan data with progress tracking
        
        Override this method in subclasses
        """
        raise NotImplementedError


# Example: Dormant Arrangement with Progress
class DormantArrangementWithProgress(ProgressAwareLoanProcessor):
    """Dormant arrangement processor with progress callbacks"""
    
    def process_with_progress(self, file_input, branch_name: str) -> Dict[str, Any]:
        """Process dormant arrangement with progress updates"""
        try:
            # Step 1: Load data (0-20%)
            self.progress.update(5, "Loading file...")
            from Dormant_Arrangement import BranchDataProcessorAPI
            
            processor = BranchDataProcessorAPI()
            
            self.progress.update(10, "Reading file content...")
            load_result = processor.load_data(file_input, "uploaded_file.xlsx")
            
            if load_result['status'] == 'error':
                return load_result
            
            self.progress.update(20, f"Loaded {load_result['data_summary']['total_records']} records")
            
            # Step 2: Process branch data (20-70%)
            self.progress.update(30, f"Processing branch: {branch_name}")
            process_result = processor.process_branch(branch_name)
            
            if process_result['status'] == 'error':
                return process_result
            
            self.progress.update(50, "Normalizing phone numbers...")
            # Phone normalization happens inside process_branch
            
            self.progress.update(60, "Removing duplicates...")
            # Deduplication happens inside process_branch
            
            self.progress.update(70, "Performing quality checks...")
            # Quality checks happen inside process_branch
            
            # Step 3: Generate output (70-100%)
            self.progress.update(80, "Generating Excel report...")
            download_result = processor.download_processed_data(branch_name, format='excel')
            
            if download_result['status'] == 'error':
                return download_result
            
            self.progress.update(90, "Finalizing...")
            
            # Complete
            self.progress.complete(f"Successfully processed {process_result['processing_summary']['total_records']} records")
            
            return {
                'status': 'success',
                'data': process_result,
                'file_data': download_result['file_data'],
                'filename': download_result['filename']
            }
            
        except ProgressCancelled:
            return {
                'status': 'cancelled',
                'message': 'Operation was cancelled by user'
            }
        except Exception as e:
            self.progress.update(
                self.progress.current_step,
                f"Error: {str(e)}",
                error=True
            )
            return {
                'status': 'error',
                'message': str(e)
            }


# Example: Arrears Collected with Progress
class ArrearsCollectedWithProgress(ProgressAwareLoanProcessor):
    """Arrears collected processor with progress callbacks"""
    
    def process_with_progress(self, sod_content: bytes, sod_filename: str,
                             cur_content: bytes, cur_filename: str,
                             officer_targets: Optional[Dict] = None) -> Dict[str, Any]:
        """Process arrears collection with progress updates"""
        try:
            from Arreas_collected import ArrearsProcessorAPI
            
            processor = ArrearsProcessorAPI()
            
            # Step 1: Load SOD file (0-20%)
            self.progress.update(5, "Loading SOD file...")
            
            # Step 2: Load Current file (20-40%)
            self.progress.update(25, "Loading current file...")
            
            # Step 3: Process data (40-70%)
            self.progress.update(45, "Validating data...")
            
            result = processor.process(
                sod_content=sod_content,
                sod_filename=sod_filename,
                cur_content=cur_content,
                cur_filename=cur_filename,
                officer_targets=officer_targets,
                output_format='json'
            )
            
            self.progress.update(60, "Calculating collections...")
            self.progress.update(70, "Generating summary...")
            
            # Step 4: Finalize (70-100%)
            self.progress.update(90, "Preparing response...")
            
            self.progress.complete("Arrears collection analysis completed")
            
            return result
            
        except ProgressCancelled:
            return {
                'status': 'cancelled',
                'message': 'Operation was cancelled by user'
            }
        except Exception as e:
            self.progress.update(
                self.progress.current_step,
                f"Error: {str(e)}",
                error=True
            )
            return {
                'status': 'error',
                'message': str(e)
            }


# Example: Arrange Arrears with Progress
class ArrangeArrearsWithProgress(ProgressAwareLoanProcessor):
    """Arrange arrears processor with progress callbacks"""
    
    def process_with_progress(self, file_input) -> Dict[str, Any]:
        """Process arrears arrangement with progress updates"""
        try:
            from arrange_arrears import EnterpriseDashboardAPI
            
            dashboard = EnterpriseDashboardAPI()
            
            # Step 1: Load data (0-30%)
            self.progress.update(10, "Loading data file...")
            
            # Step 2: Process (30-80%)
            self.progress.update(35, "Cleaning data...")
            self.progress.update(50, "Calculating risk buckets...")
            self.progress.update(65, "Sorting by sales rep...")
            
            result = dashboard.create_enterprise_dashboard(file_input)
            
            # Step 3: Generate report (80-100%)
            self.progress.update(85, "Generating Excel charts...")
            self.progress.update(95, "Applying formatting...")
            
            self.progress.complete("Enterprise dashboard created successfully")
            
            return result
            
        except ProgressCancelled:
            return {
                'status': 'cancelled',
                'message': 'Operation was cancelled by user'
            }
        except Exception as e:
            self.progress.update(
                self.progress.current_step,
                f"Error: {str(e)}",
                error=True
            )
            return {
                'status': 'error',
                'message': str(e)
            }


# Factory function to create progress-aware processors
def create_progress_processor(processor_type: str, progress_tracker: Optional[ProgressTracker] = None):
    """
    Create a progress-aware processor
    
    Args:
        processor_type: Type of processor ('dormant', 'arrears_collected', 'arrange_arrears', etc.)
        progress_tracker: Optional progress tracker instance
    
    Returns:
        Progress-aware processor instance
    """
    processors = {
        'dormant': DormantArrangementWithProgress,
        'arrears_collected': ArrearsCollectedWithProgress,
        'arrange_arrears': ArrangeArrearsWithProgress,
    }
    
    processor_class = processors.get(processor_type)
    if not processor_class:
        raise ValueError(f"Unknown processor type: {processor_type}")
    
    return processor_class(progress_tracker)
