# SafeTriage (Part 2)
# What is SafeTriage?
### SafeTriage is a program that allows users to describe a workplace hazard in normal language. An AI converts it into structured risk information, and the program applies business rules to prioritise and route the incident to the appropriate authorities.

# How does SafeTriage work?
### SafeTriage bridges natural-language reporting and operational response. AI converts each report into structured risk data, and fixed business rules then give it an objective priority and route it to the right teams. These recommendations are shown to workplace safety personnel for final review, verification or override (Human-in-the-Loop design).

# What is new in Part 2?
### -Object-oriented redesign: 49 classes, one per file, grouped into four managers (IO, AI, Logic, Data)
### -New feature: Summary Report for admins (totals, priority/status/hazard counts, hotspot locations, urgent backlog)
### -New feature: Delete a rejected incident (deleted IDs are never reused)
### -Advanced feature: SQLite database with full CRUD, alongside the original JSON file
### -Backup AI: if Gemini fails or does not reply within 30 seconds, Groq is tried automatically
### -195 automated tests, Docker and GitHub Actions CI

# Intended Users
### Employees/building occupants, facilities teams, workplace safety staff and site managers.

# What does the AI do?
### The AI converts the free-text report into structured fields such as hazard type, severity, electrical/fire/structural/water/chemical risks, injury status, people exposed and a confidence score. The AI does not make the final priority decision; the rule engine does.
### If no AI is available, the report is still saved as "Unrated" so safety staff can triage it manually.

# Features
### -Report a hazard in natural language
### -Automatic priority classification and team routing
### -Duplicate detection (same location and hazard within 4 hours)
### -Save/view/filter incident history in JSON or SQLite
### -AI risk extraction and structured JSON output, with Groq as a backup
### -A human approves, overrides or rejects before dispatch
### -Summary report and deletion of rejected incidents
### -Graceful handling of bad input, API errors, timeouts, malformed AI output and corrupt files

# How to get SafeTriage started?
## Input the following code in the terminal.
### git clone https://github.com/MahChenHan/SafeTriage.git
### cd "SafeTriage/SafeTriage_Part 2"
### Create a file called ".env" in this folder containing your own keys (never commit this file):
### GEMINI_API_KEY=your-gemini-key
### GROQ_API_KEY=your-groq-key (optional backup)
### In the terminal, input "docker build -t inf1103-safetriage ."
### NOTE: The build also runs all 195 tests and stops if any fail. SafeTriage still runs without API keys; reports are then saved as "Unrated" for manual triage.

# How to run the test script?
### In the terminal, type "docker run --rm inf1103-safetriage python -m unittest discover -s tests -p "test_safetriage.py""
### The tests need no API key or internet connection. It should end with "Ran 195 tests" and "OK".

# How to report a hazard in SafeTriage (as a user)?
### In the terminal, type "docker run --rm -it --env-file .env -v "${PWD}/data:/app/data" inf1103-safetriage python main.py user"
### This runs SafeTriage from the POV of a user reporting a hazard. Enter your name, the location and a description of the hazard. You will see the hazards detected, a provisional priority, the recommended team(s) and the recommended action.

# How to review incidents that have been reported (as an admin)?
## Input the following code in the terminal
### docker run --rm -it --env-file .env -v "${PWD}/data:/app/data" inf1103-safetriage python main.py admin
### This runs SafeTriage from the POV of an admin. Enter your Admin ID (e.g. admin01), then choose:
### 1 - Review pending incidents (most urgent first): approve, override or reject
### 2 - Incident history, filtered by status or priority
### 3 - Summary report
### 4 - Delete a rejected incident
### 5 - Quit
### The admin makes the final decision to dispatch or contact the relevant authorities.

# How to use the SQLite database instead of JSON?
### Add "-e SAFETRIAGE_STORAGE=sqlite" to the user or admin command, e.g.
### docker run --rm -it --env-file .env -e SAFETRIAGE_STORAGE=sqlite -v "${PWD}/data:/app/data" inf1103-safetriage python main.py admin
### The data is then stored in data/incidents.db instead of data/incidents.json.

# Running without Docker (optional)
### Requires Python 3.11 or newer. Put your keys in a file called "secrets_local.py" (never commit it), for example GEMINI_API_KEY = "your-key", then run:
### python main.py user
### python main.py admin
### python -m unittest discover -s tests -p "test_safetriage.py"

# Project layout
### main.py - entry point (python main.py user | admin)
### application.py - builds the four managers and starts a session
### io_manager/ - all keyboard and screen code (IOManager, Screens, InputValidator)
### ai_manager/ - AIManager, GeminiProvider, GroqProvider, FallbackAIProvider, PromptBuilder, ResponseValidator
### logic_manager/ - LogicManager, the triage rules, TeamRouter, DuplicateDetector, SummaryReportBuilder
### data_manager/ - DataManager, JSON and SQLite repositories, RepositoryFactory, FileLock
### domain/, errors/, sessions/, constants.py - shared records, exceptions, user/admin workflows and named values
### tests/test_safetriage.py - 195 unit tests
### docs/DESIGN_NOTES.md - UML diagrams, data flow, OOP/SOLID mapping and exception matrix
