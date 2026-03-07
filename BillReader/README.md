# Bill Reconciliation Tool

An automated electricity bill reconciliation tool built with Python, FastAPI, and Celery.

## Directory Structure
- `src/main.py`: FastAPI entrypoint.
- `src/celery_app.py`: Celery background task setup.
- `src/services/file_parser.py`: Parses Excel files and uses Regex to extract Consumer Numbers.
- `src/services/validation_service.py`: Contains business rules and logic.
- `src/services/processor.py`: Orchestrates validation and routes files using `shutil`.
