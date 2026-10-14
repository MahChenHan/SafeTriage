# SafeTriage
# What is SafeTriage?
### SafeTriage is a program that allow users to describe a workplace hazard in normal language. An AI converts it into structured risk information, and the program applies business rules to prioritise and route the incident to appropriate authorities. 

# How does SafeTriage work?
### SafeTriage bridges natural language reporting and operational response by using AI to convert reports into structured risk data, which is then immediately processed by deterministic procedural rules for objective priority scoring and automated dispatch. It presents these actionable recommendations to workplace safety personnel for final review, verification, or override. (Human-in-the-Loop design)

# Intended Users
### Employees/building occupants, facilities teams, workplace safety staff and site managers.

# What does the AI do?
### The AI converts the free-text report into structured fields such as hazard type, severity, electrical/fire/structural/water/chemical risks, injury status, people exposed and confidence score. The AI does not make the final priority decision; the procedural logic does.

# Potential Features
### -Report a hazard in natural language
### -Automatic priority classification and team routing
### -Save/view/filter incident history in JSON
### -AI risk extraction and structured JSON output
### -A human approves or overrides before dispatch.
### -Graceful handling of bad input, API errors, malformed AI output and file errors

# How to get SafeTriage Started?
## Input the following code in the terminal. 
### git clone https://github.com/MahChenHan/SafeTriage.git
### cd Safetriage
### open "Dockerfile"
### In the terminal, input "docker build -t inf1103-safetriage ." 
### NOTE: This will run SafeTriage WITHOUT Gemini API

# How to report a hazard in Safetriage (as a user)?
### In the terminal, type "docker run --rm inf1103-safetriage python test_logic_manager.py"
### This Docker container will run SafeTriage from the POV of a user trying to report a Hazard and its Location.

# How to review incidents that have been reported (as a admin)?
## Input the following code in the terminal
### open "Dockerfile" 
### In the terminal, input "docker run --rm -it --env-file .env -v "${PWD}/data:/app/data" inf1103-safetriage python main.py admin" 
### This will run Safetriage from the POV of a admin to review existing incidents / hazards that has been reported. The admin will make the final decision to dispatch or contact the relevant authorities.
