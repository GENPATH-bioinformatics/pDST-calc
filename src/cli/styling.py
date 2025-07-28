"""
Styling module for DST Calculator CLI
Provides color codes and utility functions for terminal output styling.
"""

import sys
from datetime import datetime

class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def supports_color():
    """Check if the terminal supports color output."""
    return hasattr(sys.stderr, "isatty") and sys.stderr.isatty()

def print_success(message):
    """Print a success message in green."""
    if supports_color():
        print(f"{Colors.GREEN}✓ {message}{Colors.END}")
    else:
        print(f"✓ {message}")

def print_error(message):
    """Print an error message in red."""
    if supports_color():
        print(f"{Colors.RED}✗ {message}{Colors.END}")
    else:
        print(f"✗ {message}")

def print_warning(message):
    """Print a warning message in yellow."""
    if supports_color():
        print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")
    else:
        print(f"⚠ {message}")

def print_info(message):
    """Print an info message in cyan."""
    if supports_color():
        print(f"{Colors.CYAN}ℹ {message}{Colors.END}")
    else:
        print(f"ℹ {message}")

def print_progress(message):
    """Print a progress message in blue."""
    if supports_color():
        print(f"{Colors.BLUE}→ {message}{Colors.END}")
    else:
        print(f"→ {message}")

def print_header():
    """
    Print a cool header similar to nf-core with ASCII art and program information.
    """
    # ASCII art for DST Calculator
    ascii_art = """
    ╔══════════════════════════════════════════════════════════════════════════════════╗
    ║                                                                                  ║
    ║    ██████╗ ██████╗  ███████╗████████╗          ██████╗ █████╗ ██╗      ██████╗   ║
    ║    ██╔══██╗██╔═══██╗██╔════╝╚══██╔══╝         ██╔════╝██╔══██╗██║     ██╔════╝   ║
    ║    ██████╔╝██║   ██║███████╗   ██║    ██████╗ ██║     ███████║██║     ██║        ║
    ║    ██╔═══╝ ██║   ██║╚════██║   ██║    ╚═════╝ ██║     ██╔══██║██║     ██║        ║
    ║    ██║     ██████╔╝ ███████║   ██║            ╚██████╗██║  ██║███████╗╚██████╗   ║
    ║    ╚═╝     ╚═════╝  ╚══════╝   ╚═╝             ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝   ║
    ║                                                                                  ║
    ║         Phenotypic Drug Susceptibility Testing Calculator                        ║
    ║                                                                                  ║
    ╚══════════════════════════════════════════════════════════════════════════════════╝
    """
    
    if supports_color():
        print(f"{Colors.CYAN}{ascii_art}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.GREEN}╔══════════════════════════════════════════════════════════════════════════════╗{Colors.END}")
        print(f"{Colors.BOLD}{Colors.GREEN}║{Colors.END}  {Colors.YELLOW}Phenotypic Drug Susceptibility Testing Calculator{Colors.END}                           {Colors.BOLD}{Colors.GREEN}║{Colors.END}")
        print(f"{Colors.BOLD}{Colors.GREEN}║{Colors.END}  {Colors.CYAN}Version:{Colors.END} 1.0.0                                                              {Colors.BOLD}{Colors.GREEN}║{Colors.END}")
        print(f"{Colors.BOLD}{Colors.GREEN}║{Colors.END}  {Colors.CYAN}Started:{Colors.END} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                                                {Colors.BOLD}{Colors.GREEN}║{Colors.END}")
        print(f"{Colors.BOLD}{Colors.GREEN}║{Colors.END}  {Colors.CYAN}Command:{Colors.END} {' '.join(sys.argv)}                                                    {Colors.BOLD}{Colors.GREEN}║{Colors.END}")
        print(f"{Colors.BOLD}{Colors.GREEN}║{Colors.END}  {Colors.CYAN}Logs:{Colors.END}    logs/pdst-calc-*.log                                               {Colors.BOLD}{Colors.GREEN}║{Colors.END}")
        print(f"{Colors.BOLD}{Colors.GREEN}║{Colors.END}  {Colors.CYAN}Results:{Colors.END} results/                                                           {Colors.BOLD}{Colors.GREEN}║{Colors.END}")
        print(f"{Colors.BOLD}{Colors.GREEN}╚══════════════════════════════════════════════════════════════════════════════╝{Colors.END}")
    else:
        # Fallback for terminals without color support
        print(ascii_art)
        print("╔══════════════════════════════════════════════════════════════════════════════╗")
        print("║  Phenotypic Drug Susceptibility Testing Calculator                          ║")
        print("║  Version: 1.0.0                                                              ║")
        print(f"║  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                                    ║")
        print(f"║  Command: {' '.join(sys.argv)}                                        ║")
        print("║  Logs:    logs/pdst-calc-*.log                                          ║")
        print("║  Results: results/                                                           ║")
        print("╚══════════════════════════════════════════════════════════════════════════════╝")
    
    print()  # Empty line for spacing

def print_step(step_number, step_title):
    """Print a step with numbering and styling."""
    if supports_color():
        print(f"\n{Colors.BOLD}{Colors.CYAN}[{step_number}]{Colors.END} {Colors.YELLOW}{step_title}{Colors.END}")
    else:
        print(f"\n[{step_number}] {step_title}")

def print_progress_bar(current, total, width=50):
    """Print a progress bar with percentage."""
    progress = int(width * current / total)
    bar = "█" * progress + "░" * (width - progress)
    percentage = int(100 * current / total)
    
    if supports_color():
        print(f"\r{Colors.BLUE}[{bar}]{Colors.END} {percentage}%", end="", flush=True)
    else:
        print(f"\r[{bar}] {percentage}%", end="", flush=True)
    
    if current == total:
        print()  # New line when complete

def print_section_header(title):
    """Print a section header with styling."""
    if supports_color():
        print(f"\n{Colors.BOLD}{Colors.BLUE}╔══════════════════════════════════════════════════════════════════════════════╗{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}║{Colors.END}  {Colors.YELLOW}{title}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}╚══════════════════════════════════════════════════════════════════════════════╝{Colors.END}")
    else:
        print(f"\n╔══════════════════════════════════════════════════════════════════════════════╗")
        print(f"║  {title}")
        print(f"╚══════════════════════════════════════════════════════════════════════════════╝")

def print_subsection(title):
    """Print a subsection header."""
    if supports_color():
        print(f"\n{Colors.BOLD}{Colors.CYAN}▶ {title}{Colors.END}")
    else:
        print(f"\n▶ {title}")

def print_instruction(message):
    """Print an instruction message."""
    if supports_color():
        print(f"{Colors.YELLOW}💡 {message}{Colors.END}")
    else:
        print(f"💡 {message}")

def print_waiting(message):
    """Print a waiting message."""
    if supports_color():
        print(f"{Colors.CYAN}⏳ {message}{Colors.END}")
    else:
        print(f"⏳ {message}")

def print_completion(message):
    """Print a completion message."""
    if supports_color():
        print(f"{Colors.GREEN}✅ {message}{Colors.END}")
    else:
        print(f"✅ {message}")

def print_table_header(title):
    """Print a table header."""
    if supports_color():
        print(f"\n{Colors.BOLD}{Colors.BLUE}┌─ {title} ─{'─' * (70 - len(title))}┐{Colors.END}")
    else:
        print(f"\n┌─ {title} ─{'─' * (70 - len(title))}┐")

def print_table_footer():
    """Print a table footer."""
    if supports_color():
        print(f"{Colors.BOLD}{Colors.BLUE}└{'─' * 72}┘{Colors.END}")
    else:
        print(f"└{'─' * 72}┘")

def print_help_text():
    """Print helpful usage information."""
    help_text = """
    📋 USAGE MODES:
    • Interactive: Run without arguments for step-by-step input
    • File-based: Use --single-test-input for automated testing
    • Batch mode: Use --test-input for multiple test cases
    
    📁 OUTPUT LOCATIONS:
    • Logs: logs/pdst-calc-{session_name}.log
    • Results: results/{filename}.txt
    
    💡 TIPS:
    • Use 'all' to select all drugs at once
    • Press Ctrl+C to exit at any time
    • Check logs for detailed calculation history
    """
    
    if supports_color():
        print(f"{Colors.CYAN}{help_text}{Colors.END}")
    else:
        print(help_text)

def print_keyboard_shortcuts():
    """Print available keyboard shortcuts."""
    shortcuts = """
    ⌨️  KEYBOARD SHORTCUTS:
    • Ctrl+C: Exit program
    • Enter: Confirm selection
    • 'all': Select all drugs
    • 'q': Quit current step
    """
    
    if supports_color():
        print(f"{Colors.YELLOW}{shortcuts}{Colors.END}")
    else:
        print(shortcuts)

def print_input_prompt(prompt, example=None, required=True):
    """Print a styled input prompt with optional example."""
    if supports_color():
        if required:
            print(f"{Colors.CYAN}📝 {prompt}{Colors.END}", end="")
        else:
            print(f"{Colors.CYAN}📝 {prompt} (optional){Colors.END}", end="")
        
        if example:
            print(f" {Colors.YELLOW}Example: {example}{Colors.END}")
        else:
            print()
    else:
        if required:
            print(f"📝 {prompt}", end="")
        else:
            print(f"📝 {prompt} (optional)", end="")
        
        if example:
            print(f" Example: {example}")
        else:
            print()

def print_validation_error(message):
    """Print a validation error message."""
    if supports_color():
        print(f"{Colors.RED}❌ {message}{Colors.END}")
    else:
        print(f"❌ {message}")

def print_validation_success(message):
    """Print a validation success message."""
    if supports_color():
        print(f"{Colors.GREEN}✓ {message}{Colors.END}")
    else:
        print(f"✓ {message}")

def print_choice_prompt(options, title="Select an option"):
    """Print a styled choice prompt."""
    if supports_color():
        print(f"\n{Colors.BOLD}{Colors.YELLOW}{title}:{Colors.END}")
    else:
        print(f"\n{title}:")
    
    for i, option in enumerate(options, 1):
        if supports_color():
            print(f"  {Colors.CYAN}{i}.{Colors.END} {option}")
        else:
            print(f"  {i}. {option}")

def print_summary_box(title, items):
    """Print a summary box with items."""
    if supports_color():
        print(f"\n{Colors.BOLD}{Colors.BLUE}┌─ {title} ─{'─' * (50 - len(title))}┐{Colors.END}")
        for item in items:
            print(f"{Colors.BOLD}{Colors.BLUE}│{Colors.END}  {item}")
        print(f"{Colors.BOLD}{Colors.BLUE}└{'─' * 52}┘{Colors.END}")
    else:
        print(f"\n┌─ {title} ─{'─' * (50 - len(title))}┐")
        for item in items:
            print(f"│  {item}")
        print(f"└{'─' * 52}┘")

def print_calculation_step(step_name, formula=None):
    """Print a calculation step with optional formula."""
    if supports_color():
        print(f"\n{Colors.BOLD}{Colors.GREEN}🔬 {step_name}{Colors.END}")
        if formula:
            print(f"{Colors.CYAN}   Formula: {formula}{Colors.END}")
    else:
        print(f"\n🔬 {step_name}")
        if formula:
            print(f"   Formula: {formula}")

def print_result_summary(results):
    """Print a formatted result summary."""
    if supports_color():
        print(f"\n{Colors.BOLD}{Colors.GREEN}📊 CALCULATION RESULTS{Colors.END}")
        print(f"{Colors.BOLD}{Colors.GREEN}╔{'═' * 60}╗{Colors.END}")
        
        for drug, values in results.items():
            print(f"{Colors.BOLD}{Colors.GREEN}║{Colors.END} {Colors.YELLOW}{drug}:{Colors.END}")
            for key, value in values.items():
                print(f"{Colors.BOLD}{Colors.GREEN}║{Colors.END}   {key}: {value}")
            print(f"{Colors.BOLD}{Colors.GREEN}║{Colors.END}")
        
        print(f"{Colors.BOLD}{Colors.GREEN}╚{'═' * 60}╝{Colors.END}")
    else:
        print(f"\n📊 CALCULATION RESULTS")
        print(f"╔{'═' * 60}╗")
        
        for drug, values in results.items():
            print(f"║ {drug}:")
            for key, value in values.items():
                print(f"║   {key}: {value}")
            print(f"║")
        
        print(f"╚{'═' * 60}╝") 