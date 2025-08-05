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
    
    print()

def print_step(step_number, step_title):
    """Print a step with numbering and styling."""
    if supports_color():
        print(f"\n{Colors.BOLD}{Colors.CYAN}[{step_number}]{Colors.END} {Colors.YELLOW}{step_title}{Colors.END}")
    else:
        print(f"\n[{step_number}] {step_title}")

def print_completion(message):
    """Print a completion message."""
    if supports_color():
        print(f"{Colors.GREEN}✅ {message}{Colors.END}")
    else:
        print(f"✅ {message}")

def print_help_text():
    """Print helpful usage information."""
    help_text = """
    📋 USAGE MODES:
    • Interactive: Run without arguments for step-by-step input
    • File-based: Use --single-test-input for automated testing
    • Batch mode: Use --test-input for multiple test cases
    
    📁 OUTPUT LOCATIONS:
    • Logs: logs/pdst-calc-{session_name}.log
    • Results: results/{filename}.txt (automatically adds .txt extension)
    
    💡 TIPS:
    • Use 'all' to select all drugs at once
    • Press Ctrl+C to exit at any time
    • Check logs for detailed calculation history
    """
    
    if supports_color():
        print(f"{Colors.CYAN}{help_text}{Colors.END}")
    else:
        print(help_text)

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