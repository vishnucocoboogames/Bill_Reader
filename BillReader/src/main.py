import logging
import uuid
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import subprocess
import platform

# In-memory storage for simple job tracking (since this is a local app)
job_statuses = {}

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Bill Reconciliation API")

# Mount the static directory to serve HTML, CSS and JS
app.mount("/static", StaticFiles(directory="static"), name="static")

class ProcessRequest(BaseModel):
    previous_month_dir: str
    current_month_dir: str
    checked_dir: str
    manual_review_dir: str

class ProcessResponse(BaseModel):
    job_id: str
    message: str

@app.get("/")
async def serve_dashboard():
    """Serves the main frontend UI."""
    return FileResponse("static/index.html")

def process_bills_sync(job_id: str, prev_month_dir: str, curr_month_dir: str, checked_dir: str, manual_review_dir: str):
    """Synchronous background processing task."""
    job_statuses[job_id] = {"status": "IN_PROGRESS"}
    try:
        from src.services.file_parser import FileParserService
        from src.services.validation_service import ValidationService
        from src.services.processor import BillProcessor

        parser = FileParserService()
        validator = ValidationService()
        processor = BillProcessor(file_parser=parser, validation_service=validator)
        
        def update_progress(processed, total):
            job_statuses[job_id]["processed"] = processed
            job_statuses[job_id]["total"] = total
            
        report_file = processor.process_directories(prev_month_dir, curr_month_dir, checked_dir, manual_review_dir, progress_callback=update_progress)
        job_statuses[job_id]["status"] = "COMPLETED"
        job_statuses[job_id]["report"] = report_file
        logger.info(f"Job {job_id} completed successfully. Report saved to {report_file}")
    except Exception as e:
        job_statuses[job_id] = {"status": "FAILED", "error": str(e)}
        logger.error(f"Job {job_id} failed: {e}")

@app.post("/process-bills", response_model=ProcessResponse)
async def process_bills(req: ProcessRequest, background_tasks: BackgroundTasks):
    """
    Accepts folder paths and triggers processing as a background task.
    Returns a job_id for tracking.
    """
    job_id = str(uuid.uuid4())
    logger.info(f"Triggering background task {job_id} for bill processing")
    
    # Path validation
    if not os.path.exists(req.previous_month_dir) or not os.path.isdir(req.previous_month_dir):
        raise HTTPException(status_code=400, detail=f"Previous month directory not found: {req.previous_month_dir}")
        
    if not os.path.exists(req.current_month_dir) or not os.path.isdir(req.current_month_dir):
        raise HTTPException(status_code=400, detail=f"Current month directory not found: {req.current_month_dir}")

    # Dispatch to FastAPI BackgroundTasks
    background_tasks.add_task(
        process_bills_sync, 
        job_id, 
        req.previous_month_dir, 
        req.current_month_dir, 
        req.checked_dir, 
        req.manual_review_dir
    )
    
    return ProcessResponse(
        job_id=job_id, 
        message="Bill processing triggered successfully."
    )

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """Real endpoint to check background task status."""
    status_data = job_statuses.get(job_id, {"status": "PENDING"})
    
    response = {
        "job_id": job_id,
        "status": status_data["status"],
    }
    
    if "processed" in status_data and "total" in status_data:
        response["processed"] = status_data["processed"]
        response["total"] = status_data["total"]
    
    if status_data["status"] == 'COMPLETED':
        response["report"] = status_data["report"]
    elif status_data["status"] == 'FAILED':
        response["error"] = status_data["error"]
        
    return response

@app.get("/api/select-folder")
async def select_folder():
    """Opens a native folder selection dialog (Mac/Windows) and returns the path."""
    try:
        sys_name = platform.system()
        path = ""
        
        if sys_name == 'Darwin':
            # AppleScript for macOS
            script = '''
            tell application (path to frontmost application as text)
                set folderPath to choose folder with prompt "Select Folder"
                return POSIX path of folderPath
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
            if result.returncode == 0:
                path = result.stdout.strip()
                
        elif sys_name == 'Windows':
            # PowerShell for Windows
            script = '''
            Add-Type -AssemblyName System.windows.forms
            $browser = New-Object System.Windows.Forms.FolderBrowserDialog
            $browser.Description = "Select Folder"
            if ($browser.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
                Write-Output $browser.SelectedPath
            }
            '''
            result = subprocess.run(["powershell", "-sta", "-Command", script], capture_output=True, text=True)
            if result.returncode == 0:
                path = result.stdout.strip()
                
        else:
            # Fallback for Linux using tkinter
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                path = filedialog.askdirectory()
                root.destroy()
            except ImportError:
                return {"error": "Unsupported OS for native file picker widget."}
                
        if path:
            return {"path": path}
        else:
            return {"error": "Folder selection cancelled or failed."}
            
    except Exception as e:
        return {"error": str(e)}
