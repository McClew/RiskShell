import cmd
import fnmatch
import os
import sys
from rich.console import Console
from rich.table import Table
from app.engine import SafeFormulaEvaluator, load_risk_modules
import plotext as plt
import numpy as np
import math

def calculate_clean_ticks(min_val, max_val, num_ticks=5):
    if num_ticks < 2:
        num_ticks = 2
    range_val = max_val - min_val
    if range_val <= 0:
        return [min_val]
        
    rough_step = range_val / (num_ticks - 1)
    
    scale = 10 ** math.floor(math.log10(rough_step))
    normalized_step = rough_step / scale
    
    if normalized_step < 1.5:
        nice_step = 1
    elif normalized_step < 3:
        nice_step = 2
    elif normalized_step < 7:
        nice_step = 5
    else:
        nice_step = 10
        
    step = nice_step * scale
    
    start_tick = math.floor(min_val / step) * step
    end_tick = math.ceil(max_val / step) * step
    
    ticks = []
    current = start_tick
    while current <= end_tick + step / 10:
        ticks.append(current)
        current += step
        
    return ticks

console = Console()

# ANSI escape sequences for terminal styling
RESET = "\033[0m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
WHITE = "\033[97m"
GREY = "\033[90m"

class RiskShell(cmd.Cmd):
    intro = (
        f"\n{BOLD}{MAGENTA}=================================================================={RESET}\n"
        f"  {BOLD}{CYAN}RiskShell :: Cybersecurity Risk Assessment{RESET}\n"
        f"  {GREY}Authoritative risk analysis, calculation, and decision-support tool.{RESET}\n"
        f"  {BOLD}{MAGENTA}================================================================{RESET}\n"
        f"  Type {BOLD}{YELLOW}help{RESET} to display available commands. Type {BOLD}{YELLOW}exit{RESET} to quit.\n"
    )
    prompt = f"{BOLD}{GREEN}risk> {RESET}"

    def __init__(self, app_dir):
        super().__init__()
        self.app_dir = app_dir
        # Load all schema-valid modules recursively
        self.modules = load_risk_modules(self.app_dir)
        
        # Assign stable IDs based on sorted module keys
        self.modules_by_id = {}
        for idx, key in enumerate(sorted(self.modules.keys())):
            self.modules[key]['id'] = idx
            self.modules_by_id[idx] = key
        
        # State tracking
        self.active_module_key = None
        self.active_module = None
        self.current_variables = {}
        
        # Enable ANSI capabilities in Windows Command Prompt if needed
        if os.name == 'nt':
            os.system('')

    def preloop(self):
        print(f"Loaded {len(self.modules)} risk assessment modules successfully.")

    def do_help(self, arg):
        # Show context-aware help menus
        if self.active_module:
            print(f"\n{BOLD}{CYAN}Active Module Commands ({self.active_module['title']}){RESET}")
            print(f"{GREY}-------------------------------------------------------------{RESET}")
            print(f"  {BOLD}{YELLOW}show info{RESET}       : Display the module's methodology, pros, cons, and sources.")
            print(f"  {BOLD}{YELLOW}show options{RESET}    : View current variables, values, and default values.")
            print(f"  {BOLD}{YELLOW}set [var] [val]{RESET} : Modify a variable's value within the current context.")
            print(f"  {BOLD}{YELLOW}go{RESET}              : Execute the mathematical evaluation and print a detailed trace.")
            print(f"  {BOLD}{YELLOW}back{RESET}            : Return to the root menu (unloads active module).")
        else:
            print(f"\n{BOLD}{CYAN}Global Commands (Root Context){RESET}")
            print(f"{GREY}-------------------------------------------------------------{RESET}")
            print(f"  {BOLD}{YELLOW}search [keyword]{RESET} : Search modules by path, title, description, or methodology. Use 'search *' to show all modules.")
            print(f"  {BOLD}{YELLOW}use [module]{RESET}     : Switch context into a specific risk module.")
            
        print(f"  {BOLD}{YELLOW}help{RESET}             : Show this context-aware help menu.")
        print(f"  {BOLD}{YELLOW}clear{RESET}            : Clear the terminal screen.")
        print(f"  {BOLD}{YELLOW}exit{RESET} / {BOLD}{YELLOW}quit{RESET}      : Exit the risk assessment programme.\n")

    def default(self, line):
        cmd_name = line.split()[0] if line.split() else line
        print(f"{BOLD}{RED}Error: Unknown command '{cmd_name}'.{RESET} Type '{BOLD}help{RESET}' to see available commands.")

    # :: Global Commands

    def do_search(self, arg):
        # Recursively search paths, names, summaries, or target impacts across all YAML modules
        if not arg.strip():
            print(f"{BOLD}{YELLOW}Warning: Please specify a search keyword (e.g., 'search phishing').{RESET}")
            return
            
        keyword = arg.strip().lower()
        
        # If the search term has no wildcard symbols, treat it as a standard substring search
        if '*' not in keyword and '?' not in keyword:
            pattern = f"*{keyword}*"
        else:
            pattern = keyword
            
        def matches_pattern(text):
            if not text:
                return False
            return fnmatch.fnmatch(str(text).lower(), pattern)
            
        matches = []
        for key, mod in self.modules.items():
            path_match = matches_pattern(mod.get('module_key', ''))
            title_match = matches_pattern(mod.get('title', ''))
            desc_match = matches_pattern(mod.get('description', ''))
            meth_match = matches_pattern(mod.get('methodology', ''))
            
            # Check pros and cons lists
            pros_match = any(matches_pattern(pro) for pro in mod.get('pros', []))
            cons_match = any(matches_pattern(con) for con in mod.get('cons', []))
            
            if path_match or title_match or desc_match or meth_match or pros_match or cons_match:
                matches.append(mod)
                
        if not matches:
            print(f"No risk modules matched the pattern: '{arg}'.")
            return
            
        print(f"\nFound {len(matches)} matching risk module(s):\n")
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("ID")
        table.add_column("Module Path")
        table.add_column("Title")
        table.add_column("Description")
        for mod in matches:
            # Truncate description for clean display
            desc = mod.get('description', '').strip().replace('\n', ' ')
            if len(desc) > 60:
                desc = desc[:57] + "..."
            table.add_row(str(mod['id']), mod['module_key'], mod['title'], desc)
            
        console.print(table)
        console.print()

    def do_use(self, arg):
        # Switch context into a specific risk module
        if not arg.strip():
            print(f"{BOLD}{YELLOW}Warning: Please specify a module path or ID (e.g., 'use modules/microsoft_dread' or 'use 0').{RESET}")
            return
            
        target = arg.strip().replace('\\', '/')
        matched_mod = None
        
        # Try matching by ID first if the target is a numeric digit
        if target.isdigit():
            target_id = int(target)
            if target_id in self.modules_by_id:
                matched_mod = self.modules[self.modules_by_id[target_id]]
            else:
                print(f"{BOLD}{RED}Error: Risk module ID '{target_id}' not found.{RESET}")
                print("Use 'search [keyword]' to discover available modules and their IDs.")
                return
        
        # Try matching by exact key
        if not matched_mod and target in self.modules:
            matched_mod = self.modules[target]
        
        if not matched_mod:
            # Try partial match on the key
            for key, mod in self.modules.items():
                if target in key or key in target:
                    matched_mod = mod
                    break
            
            # Try matching title
            if not matched_mod:
                for key, mod in self.modules.items():
                    if target.lower() in mod.get('title', '').lower():
                        matched_mod = mod
                        break
                        
        if not matched_mod:
            print(f"{BOLD}{RED}Error: Risk module '{target}' not found.{RESET}")
            print("Use 'search [keyword]' to discover available modules.")
            return
            
        # Switch context
        self.active_module_key = matched_mod['module_key']
        self.active_module = matched_mod
        
        # Load variables with default values
        self.current_variables = {}
        for var in matched_mod.get('variables', []):
            self.current_variables[var['name']] = var.get('default')
            
        self.prompt = f"{BOLD}{GREEN}risk({self.active_module_key})> {RESET}"
        print(f"\n{BOLD}{GREEN}Switched context to: {matched_mod['title']}{RESET}")
        print(f"{matched_mod['description'].strip()}\n")
        print("Type 'show options' to review variable settings or 'go' to calculate.")

    def complete_use(self, text, line, begidx, endidx):
        completions = list(self.modules.keys()) + [str(mod['id']) for mod in self.modules.values()]
        return [c for c in completions if c.startswith(text)]

    # :: Active Context Commands

    def do_show(self, arg):
        # Display metadata for the active module
        if not self.active_module:
            print(f"{BOLD}{RED}Error: No active module loaded.{RESET} Switch to a module first using 'use [module]'.")
            return
            
        args = arg.strip().split()
        subcommand = args[0].lower() if args else ""
        
        if subcommand == "info":
            self._show_info()
        elif subcommand == "options":
            self._show_options()
        else:
            print(f"{BOLD}{RED}Error: Invalid subcommand for show.{RESET} Use 'show info' or 'show options'.")

    def complete_show(self, text, line, begidx, endidx):
        subcmds = ["info", "options"]
        return [s for s in subcmds if s.startswith(text)]

    def _show_info(self):
        mod = self.active_module
        console.print(f"\n[bold cyan]Title: {mod['title']}[/bold cyan]")
        console.print(f"[bold cyan]File Path: {mod['file_path']}[/bold cyan]\n")
        
        console.print(f"[bold underline]Description:[/bold underline]")
        console.print(mod['description'].strip())
        console.print()
        
        console.print(f"[bold underline]Methodology:[/bold underline]")
        console.print(mod['methodology'].strip())
        console.print()
        
        console.print(f"[bold underline]Pros & Cons Analysis:[/bold underline]")
        console.print(" [bold green]Pros:[/bold green]")
        for pro in mod.get('pros', []):
            console.print(f"   - {pro}")
        console.print(" [bold red]Cons:[/bold red]")
        for con in mod.get('cons', []):
            console.print(f"   - {con}")
        console.print()
        
        # Gather unique sources from variables and display them
        sources = set()
        for var in mod.get('variables', []):
            if var.get('source'):
                sources.add(var['source'])
                
        console.print(f"[bold underline]Reference Sources:[/bold underline]")
        if sources:
            for src in sorted(sources):
                console.print(f"   - {src}")
        else:
            console.print("   - No reference sources recorded for this module.")
        console.print()

    def _show_options(self):
        mod = self.active_module
        console.print(f"\n[bold cyan]Current Configuration Options for: {mod['title']}[/bold cyan]")
        if 'script' in mod:
            console.print(f"Script:\n[bold yellow]{mod['script']}[/bold yellow]\n")
        else:
            console.print(f"Formula: [bold yellow]{mod['formula']}[/bold yellow]\n")
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Variable")
        table.add_column("Current Value")
        table.add_column("Required?")
        table.add_column("Default")
        table.add_column("Description")
        table.add_column("Source")
        
        for var in mod.get('variables', []):
            name = var['name']
            val = self.current_variables.get(name)
            val_str = "None" if val is None else str(val)
            req_str = "Yes" if var.get('required', False) else "No"
            default_str = str(var.get('default', 'None'))
            desc = var.get('description', '')
            src = var.get('source', '')
            
            table.add_row(name, val_str, req_str, default_str, desc, src)
            
        console.print(table)
        console.print()

    def do_set(self, arg):
        # Modify a variable's value within the current context
        if not self.active_module:
            print(f"{BOLD}{RED}Error: No active module loaded.{RESET} Load a module first using 'use [module]'.")
            return
            
        parts = arg.strip().split(maxsplit=1)
        if len(parts) < 2:
            print(f"{BOLD}{RED}Error: Missing arguments.{RESET} Use: 'set [variable_name] [value]'.")
            return
            
        var_name, val_str = parts[0], parts[1]
        
        # Validate that variable is part of the module
        allowed_vars = {v['name']: v for v in self.active_module.get('variables', [])}
        if var_name not in allowed_vars:
            print(f"{BOLD}{RED}Error: Variable '{var_name}' is not defined in this module.{RESET}")
            print(f"Available variables: {', '.join(allowed_vars.keys())}")
            return
            
        # Parse value as numeric
        try:
            if '.' in val_str:
                val = float(val_str)
            else:
                val = int(val_str)
        except ValueError:
            print(f"{BOLD}{RED}Error: Value '{val_str}' must be numeric (integer or float).{RESET}")
            return
            
        self.current_variables[var_name] = val
        print(f"Variable {BOLD}{CYAN}{var_name}{RESET} updated to: {BOLD}{GREEN}{val}{RESET}")

    def complete_set(self, text, line, begidx, endidx):
        if not self.active_module:
            return []
        vars_list = [v['name'] for v in self.active_module.get('variables', [])]
        return [v for v in vars_list if v.startswith(text)]

    def do_back(self, arg):
        # Move out of an active module back to the root prompt
        if not self.active_module:
            print("Already at the root prompt context.")
            return
            
        print(f"Unloaded module: {self.active_module['title']}. Returned to root.")
        self.active_module_key = None
        self.active_module = None
        self.current_variables = {}
        self.prompt = f"{BOLD}{GREEN}risk> {RESET}"

    def do_go(self, arg):
        # Execute the mathematical evaluation and return a detailed step-by-step trace
        if not self.active_module:
            print(f"{BOLD}{RED}Error: No active module loaded.{RESET} Load a module first using 'use [module]'.")
            return
            
        # Check required variables
        missing_vars = []
        for var in self.active_module.get('variables', []):
            if var.get('required', False) and self.current_variables.get(var['name']) is None:
                missing_vars.append(var['name'])
                
        if missing_vars:
            print(f"{BOLD}{RED}Error: Cannot compute. The following required variables are not set: {', '.join(missing_vars)}{RESET}")
            print("Please define them using 'set [variable] [value]' before running calculation.")
            return
            
        print(f"\n{BOLD}{CYAN}Initiating Risk Calculation Engine...{RESET}")
        print(f"Module: {self.active_module['title']}")
        if 'script' in self.active_module:
            print("Script: (Python Block)")
        else:
            print(f"Formula: {self.active_module['formula']}")
        print(f"{GREY}-------------------------------------------------------------{RESET}")
        
        # Display inputs
        print(f"{BOLD}Bound Variable Inputs:{RESET}")
        for k, v in self.current_variables.items():
            print(f"  - {k} = {v}")
        print()
        
        # Evaluate
        if 'script' in self.active_module:
            print(f"\n{BOLD}{RED}WARNING: You are attempting to execute a \"script\" module which will execute code directly on your device.{RESET}")
            choice = input(f"Do you wish to continue? [y/N]: ").strip().lower()
            if choice not in ['y', 'yes']:
                print("Execution cancelled.\n")
                return
                
            try:
                local_vars = self.current_variables.copy()
                exec(self.active_module['script'], globals(), local_vars)
                
                if 'visualisation' in self.active_module:
                    print(f"\n{BOLD}{CYAN}Visualisation:{RESET}")
                    self._render_visualisation(self.active_module['visualisation'], local_vars)
                    
                print(f"{GREY}-------------------------------------------------------------{RESET}\n")
            except Exception as e:
                print(f"{BOLD}{RED}Script Execution Error: {e}{RESET}\n")
        else:
            evaluator = SafeFormulaEvaluator(self.current_variables)
            try:
                result, steps = evaluator.evaluate(self.active_module['formula'])
                
                # Print execution trace
                print(f"{BOLD}Execution Trace (Order of Operations):{RESET}")
                for idx, step in enumerate(steps, 1):
                    print(f"  Step {idx}: {step}")
                print()
                
                # Final output formatting
                prefix = self.active_module.get('output_prefix', '')
                postfix = self.active_module.get('output_postfix', '')
                output_title = self.active_module.get('output_title', 'Calculated Risk Score:')
                
                # Currency formatting check (£)
                if result is not None:
                    if isinstance(result, str):
                        formatted_result = f"{prefix}{result}{postfix}"
                    else:
                        if prefix == "£":
                            formatted_value = f"{result:,.2f}"
                        else:
                            formatted_value = f"{result:.4f}".rstrip('0').rstrip('.')
                        formatted_result = f"{prefix}{formatted_value}{postfix}"
                        
                    print(f"{BOLD}{GREEN}{output_title}{RESET} {BOLD}{YELLOW}{formatted_result}{RESET}")
                
                print(f"{GREY}-------------------------------------------------------------{RESET}\n")
                
            except Exception as e:
                print(f"{BOLD}{RED}Evaluation Error: {e}{RESET}\n")

    def _render_visualisation(self, vis_config, vars_dict):
        try:
            plt.clear_figure()
            if 'title' in vis_config:
                plt.title(vis_config['title'])

            vis_type = vis_config['type']
            
            if vis_type == 'histogram':
                data = vars_dict.get(vis_config['data_variable'])
                if data is None:
                    print(f"{BOLD}{RED}Visualisation Error: data_variable '{vis_config['data_variable']}' not found in execution context.{RESET}")
                    return
                
                if 'visualisation_bounds' in self.active_module:
                    bounds = self.active_module['visualisation_bounds']
                    if 'x_max_percentile' in bounds:
                        p_val = np.percentile(data, bounds['x_max_percentile'])
                        data = [d for d in data if d <= p_val]
                    if 'x_max_clamp' in bounds:
                        data = [d for d in data if d <= bounds['x_max_clamp']]
                    if 'x_min_clamp' in bounds:
                        data = [d for d in data if d >= bounds['x_min_clamp']]

                bins = vis_config.get('bins', 50)
                kwargs = {}
                if 'colour' in vis_config:
                    kwargs['color'] = vis_config['colour']
                plt.hist(data, bins=bins, **kwargs)
                
                if data:
                    min_x, max_x = min(data), max(data)
                    if 'x_ticks' in vis_config:
                        x_ticks = calculate_clean_ticks(min_x, max_x, vis_config['x_ticks'])
                        x_labels = [str(int(t)) if isinstance(t, (int, float)) and float(t).is_integer() else str(t) for t in x_ticks]
                        plt.xticks(x_ticks, x_labels)
                        plt.xlim(min(x_ticks), max(x_ticks))
                    
                    if 'y_ticks' in vis_config:
                        counts, _ = np.histogram(data, bins=bins)
                        max_freq = max(counts) if len(counts) > 0 else 0
                        y_ticks = calculate_clean_ticks(0, max_freq, vis_config['y_ticks'])
                        y_labels = [str(int(t)) if isinstance(t, (int, float)) and float(t).is_integer() else str(t) for t in y_ticks]
                        plt.yticks(y_ticks, y_labels)
                        plt.ylim(min(y_ticks), max(y_ticks))
            elif vis_type in ['scatter', 'plot', 'bar']:
                x_data = vars_dict.get(vis_config['x_variable'])
                y_data = vars_dict.get(vis_config['y_variable'])
                if x_data is None:
                    print(f"{BOLD}{RED}Visualisation Error: x_variable '{vis_config['x_variable']}' not found.{RESET}")
                    return
                if y_data is None:
                    print(f"{BOLD}{RED}Visualisation Error: y_variable '{vis_config['y_variable']}' not found.{RESET}")
                    return
                
                if 'visualisation_bounds' in self.active_module:
                    bounds = self.active_module['visualisation_bounds']
                    filtered = list(zip(x_data, y_data))
                    
                    if 'x_max_percentile' in bounds:
                        p_val = np.percentile(x_data, bounds['x_max_percentile'])
                        filtered = [(x, y) for x, y in filtered if x <= p_val]
                    if 'x_max_clamp' in bounds:
                        filtered = [(x, y) for x, y in filtered if x <= bounds['x_max_clamp']]
                    if 'x_min_clamp' in bounds:
                        filtered = [(x, y) for x, y in filtered if x >= bounds['x_min_clamp']]
                        
                    if filtered:
                        x_data, y_data = zip(*filtered)
                        x_data, y_data = list(x_data), list(y_data)
                    else:
                        x_data, y_data = [], []
                
                kwargs = {}
                if 'colour' in vis_config:
                    kwargs['color'] = vis_config['colour']
                    
                if vis_type == 'scatter':
                    plt.scatter(x_data, y_data, **kwargs)
                elif vis_type == 'plot':
                    plt.plot(x_data, y_data, **kwargs)
                elif vis_type == 'bar':
                    plt.bar(x_data, y_data, **kwargs)
                    
                if x_data and y_data:
                    is_x_numeric = not any(isinstance(x, str) for x in x_data)
                    if 'x_ticks' in vis_config and is_x_numeric:
                        x_ticks = calculate_clean_ticks(min(x_data), max(x_data), vis_config['x_ticks'])
                        x_labels = [str(int(t)) if isinstance(t, (int, float)) and float(t).is_integer() else str(t) for t in x_ticks]
                        plt.xticks(x_ticks, x_labels)
                        plt.xlim(min(x_ticks), max(x_ticks))
                    is_y_numeric = not any(isinstance(y, str) for y in y_data)
                    if 'y_ticks' in vis_config and is_y_numeric:
                        y_ticks = calculate_clean_ticks(min(y_data), max(y_data), vis_config['y_ticks'])
                        y_labels = [str(int(t)) if isinstance(t, (int, float)) and float(t).is_integer() else str(t) for t in y_ticks]
                        plt.yticks(y_ticks, y_labels)
                        plt.ylim(min(y_ticks), max(y_ticks))
                        
            if 'x_label' in vis_config:
                plt.xlabel(vis_config['x_label'])
            if 'y_label' in vis_config:
                plt.ylabel(vis_config['y_label'])
            if 'theme' in vis_config:
                plt.theme(vis_config['theme'])
            if 'grid' in vis_config:
                plt.grid(vis_config['grid'], vis_config['grid'])
                
            w = vis_config.get('width')
            h = vis_config.get('height')
            if w is not None or h is not None:
                plt.plotsize(w, h)
                    
            if 'visualisation_bounds' in self.active_module:
                bounds = self.active_module['visualisation_bounds']
                left = bounds.get('x_min_clamp')
                right = bounds.get('x_max_clamp')
                if left is not None or right is not None:
                    plt.xlim(left=left, right=right)

            plt.show()
            print()
        except Exception as e:
            print(f"{BOLD}{RED}Visualisation Error: {e}{RESET}")

    # :: App Shell Lifecycle

    def do_exit(self, arg):
        # Exit the risk assessment CLI programme
        print(f"\nExiting RiskShell.{RESET}")
        return True

    def do_quit(self, arg):
        # Exit the risk assessment CLI programme
        return self.do_exit(arg)

    def do_clear(self, arg):
        # Clear the terminal screen
        os.system('cls' if os.name == 'nt' else 'clear')
