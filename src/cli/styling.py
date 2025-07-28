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

def print_step(step_number, step_title):
    """Print a step with numbering and styling."""
    if supports_color():
        print(f"\n{Colors.BOLD}{Colors.CYAN}[{step_number}]{Colors.END} {Colors.YELLOW}{step_title}{Colors.END}")
    else:
        print(f"\n[{step_number}] {step_title}") 