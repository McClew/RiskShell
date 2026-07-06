# RiskShell CLI

A modular, data-driven tool for calculating and analysing cyber security risks. 

RiskShell recursively scans, registers, and loads risk models defined externally as YAML files.

---

## Installation & Launch

### Prerequisites
- Python 3.7 or later installed on your system.

### Step 1: Install Dependencies
Install the required packages (specifically `PyYAML`) by running:
```powershell
python -m pip install -r requirements.txt
```

### Step 2: Run the Program
Launch the interactive shell:
```powershell
python riskshell.py
```

---

## Interactive Command Set

Upon boot, you will enter the global shell prompt (`risk> `). Once you select a risk model, your context switches to the active module prompt (`risk(modules/[module_name])> `).

### Global Commands (Root Context)
- `help` — Displays context-aware assistance.
- `search [keyword]` — Searches modules by path and title.
- `use [module_path]` — Switches context into a specific risk module (e.g. `use modules/annualised_loss_expectancy`). Supports partial path and title matching with auto-completion.
- `exit` / `quit` — Exits the programme.

### Active Module Commands (Contextual)
- `show info` — Prints comprehensive metadata of the active module (Title, Description, Methodology, Pros/Cons, and Reference Sources).
- `show options` — Displays a table of variables, their current values, whether they are required, defaults, descriptions, and sources.
- `set [variable] [value]` — Modifies a variable's value within the current context. Supports tab auto-completion of variable names.
- `go` — Executes the mathematical formula, validates that all required parameters are set, and prints a step-by-step trace of intermediate evaluations.
- `back` — Exits the active module and returns to the root shell prompt.

---

## Designing and Adding Custom Modules

You can easily extend the tool by creating new risk modules. The application recursively scans the `app/modules/` directory at startup, meaning you can add new YAML files directly or organise them inside categorised subdirectories (e.g. `app/modules/scenarios/`).

### Schema Requirements
Each custom module must be a schema-compliant YAML file (`.yaml` or `.yml`) containing the following keys:

- `title` (string): The human-readable name of the risk assessment model.
- `description` (string): A summary of the scenario or assessment scope.
- `methodology` (string): Detail of how calculations are structured and used.
- `pros` (sequence of strings): A list of advantages of this model.
- `cons` (sequence of strings): A list of limitations of this model.
- `variables` (sequence of mappings): The list of required and optional inputs. Each variable must include:
  - `name` (string): The variable identifier used in the mathematical formula.
  - `default` (float/int/null): The default value bound to the variable on load.
  - `required` (boolean): Flag indicating if a value must be set before calculation.
  - `description` (string): Purpose and context of the variable.
  - `source` (string): The origin or reference for obtaining the value.
- `formula` (string): A mathematical expression using standard operators (`+`, `-`, `*`, `/`, `**`) and variable names. No function calls are permitted for security.
- `output_title` (string): Required output label shown alongside calculation results (e.g. `"Risk Reduction from MFA:"`).
- `output_prefix` (string): Optional prefix string prepended to the final value (e.g. `"£"`).
- `output_postfix` (string): Optional postfix string appended to the final value (e.g. `"%"`).

### Example Custom Module Template
Create a file, e.g. `app/modules/custom_malware_cost.yaml`:

```yaml
title: "Custom Malware Recovery Cost"
description: |
  Analyses the projected cost of recovering from a targeted ransomware incident.
methodology: |
  Calculates the total financial impact by adding containment efforts, recovery activities, and business interruption losses.
pros:
  - "Provides structured categorisation of recovery costs."
  - "Simple to configure for customised corporate scenarios."
cons:
  - "Does not account for regulatory fines or reputational damage."
variables:
  - name: "ContainmentCost"
    default: 5000.0
    required: true
    description: "Monetary cost of immediate containment in GBP."
    source: "Incident Response team averages."
  - name: "SystemCount"
    default: 10
    required: true
    description: "Number of compromised systems requiring full rebuild."
    source: "IT asset database."
  - name: "RebuildCostPerSystem"
    default: 750.0
    required: true
    description: "Average cost to rebuild a single server or endpoint."
    source: "Managed Service Provider service level agreement."
  - name: "BusinessInterruptionCost"
    default: 15000.0
    required: false
    description: "Estimated cost of lost productivity during downtime."
    source: "Finance team business impact analysis."
formula: "ContainmentCost + (SystemCount * RebuildCostPerSystem) + BusinessInterruptionCost"
output_title: "Total Malware Incident Recovery Cost:"
output_prefix: "£"
```

Once saved under `app/modules/`, boot the programme (`python riskshell.py`) and use it:
```powershell
risk> use modules/custom_malware_cost
```
