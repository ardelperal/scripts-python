# Gemini Project Analysis

This document provides a summary of the project's conventions, tools, and commands to help Gemini assist you more effectively.

## Project Overview

This project is a Python-based system for managing and automating business tasks, migrated from a legacy VBS system. The core of the project is the `run_master.py` script, which acts as a continuous monitoring daemon, executing various modules according to a schedule.

## Key Technologies and Tools

*   **Programming Language:** Python 3.11+
*   **Package Manager:** pip with `requirements.txt`
*   **Testing:** `pytest` for unit, integration, and functional tests.
*   **Code Coverage:** `coverage.py` with HTML reports.
*   **Linting/Formatting:** `black`, `flake8`, `mypy`.
*   **Database:** Microsoft Access, accessed via `pyodbc` and `pywin32`.
*   **Data Processing:** `pandas`
*   **Configuration:** `python-dotenv` for environment variables.

## Project Structure

The project is organized into the following main directories:

*   `src/`: Contains the main source code, organized by module (`agedys`, `brass`, `correos`, etc.) and a `common` directory for shared utilities.
*   `scripts/`: Contains the main execution scripts, including the master runner (`run_master.py`).
*   `tests/`: Contains all tests, organized into `unit`, `integration`, and `functional` subdirectories.
*   `config/`: Contains environment variable templates.
*   `dbs-locales/`: Contains local Access databases for development.
*   `docs/`: Contains project documentation.
*   `legacy/`: Contains the original VBS scripts.
*   `tools/`: Contains development and utility scripts.

## Environments

The project supports two environments, configured via the `ENVIRONMENT` variable in the `.env` file:

*   `local`: Uses local Access databases in `dbs-locales/` and a local SMTP server (MailHog).
*   `oficina`: Uses network-based Access databases and the corporate SMTP server.

## Commands

### Installation

```bash
pip install -r requirements.txt
```

### Running the Application

The main entry point is the `run_master.py` script:

```bash
# Run the master script in continuous mode
python scripts/run_master.py

# Run with verbose logging
python scripts/run_master.py --verbose
```

Individual modules can also be run separately:

```bash
python scripts/run_agedys.py
python scripts/run_brass.py
# ...and so on for other modules
```

### Testing

Tests are run using `pytest`:

```bash
# Run all tests
pytest

# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Generate a coverage report
pytest --cov=src --cov-report=html
```

### Linting and Formatting

```bash
# Format code with black
black .

# Check for style issues with flake8
flake8 .

# Check for type errors with mypy
mypy .
```

## Gemini's Role

Based on this analysis, I can help with the following:

*   **Understanding the code:** I can explain the functionality of different modules and how they interact.
*   **Writing and running tests:** I can create new tests for existing or new functionality and run them for you.
*   **Debugging issues:** I can help you debug problems by analyzing logs and running scripts in verbose mode.
*   **Adding new features:** I can help you add new modules or extend existing ones, following the established conventions.
*   **Refactoring code:** I can help you refactor the code to improve its structure and maintainability.
