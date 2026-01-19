#!/usr/bin/env python3
"""
Security Audit Script for Nexus Risk Platform
Checks for common security issues before deployment
"""

import os
import re
import sys
from pathlib import Path

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def print_pass(msg):
    print(f"{GREEN}✓ PASS:{RESET} {msg}")

def print_fail(msg):
    print(f"{RED}✗ FAIL:{RESET} {msg}")

def print_warn(msg):
    print(f"{YELLOW}⚠ WARN:{RESET} {msg}")

def print_header(msg):
    print(f"\n{'='*50}")
    print(f" {msg}")
    print(f"{'='*50}")


class SecurityAuditor:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues = []
        self.warnings = []
        
    def run_all_checks(self):
        """Run all security checks"""
        print_header("NEXUS RISK PLATFORM - SECURITY AUDIT")
        
        self.check_env_in_gitignore()
        self.check_hardcoded_secrets()
        self.check_error_handling()
        self.check_cors_config()
        self.check_logs_in_gitignore()
        
        self.print_summary()
        return len(self.issues) == 0
    
    def check_env_in_gitignore(self):
        """Verify .env is in .gitignore"""
        print_header("Checking .gitignore for .env")
        
        gitignore_path = self.project_root / ".gitignore"
        if not gitignore_path.exists():
            self.issues.append(".gitignore not found")
            print_fail(".gitignore file not found!")
            return
        
        content = gitignore_path.read_text()
        if ".env" in content:
            print_pass(".env is listed in .gitignore")
        else:
            self.issues.append(".env not in .gitignore")
            print_fail(".env is NOT in .gitignore - secrets may be committed!")
    
    def check_hardcoded_secrets(self):
        """Scan source files for hardcoded API keys"""
        print_header("Scanning for Hardcoded Secrets")
        
        # Patterns that look like API keys
        secret_patterns = [
            (r'sk-[a-zA-Z0-9]{20,}', 'OpenAI API Key'),
            (r'AIza[a-zA-Z0-9_-]{35}', 'Google API Key'),
            (r'AKIA[A-Z0-9]{16}', 'AWS Access Key'),
            (r'ghp_[a-zA-Z0-9]{36}', 'GitHub Token'),
        ]
        
        # Directories to skip
        skip_dirs = {'venv', 'node_modules', '.git', '__pycache__', '.next'}
        
        # Files to check
        extensions = {'.py', '.ts', '.tsx', '.js', '.jsx'}
        
        found_secrets = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for file in files:
                if Path(file).suffix in extensions:
                    filepath = Path(root) / file
                    try:
                        content = filepath.read_text(errors='ignore')
                        for pattern, name in secret_patterns:
                            if re.search(pattern, content):
                                rel_path = filepath.relative_to(self.project_root)
                                found_secrets.append((rel_path, name))
                    except Exception:
                        pass
        
        if found_secrets:
            for path, secret_type in found_secrets:
                self.issues.append(f"Possible {secret_type} in {path}")
                print_fail(f"Possible {secret_type} found in {path}")
        else:
            print_pass("No hardcoded secrets detected in source files")
    
    def check_error_handling(self):
        """Verify error handler doesn't expose internals"""
        print_header("Checking Error Handling")
        
        error_handler = self.project_root / "backend" / "app" / "core" / "error_handler.py"
        
        if not error_handler.exists():
            self.warnings.append("error_handler.py not found")
            print_warn("error_handler.py not found - check error handling manually")
            return
        
        content = error_handler.read_text()
        
        # Check for secure patterns
        if "SecureErrorMiddleware" in content:
            print_pass("SecureErrorMiddleware is implemented")
        else:
            self.warnings.append("SecureErrorMiddleware not found")
            print_warn("SecureErrorMiddleware not found")
        
        # Check that stack traces aren't returned to users
        if "traceback" in content.lower():
            if "log" in content.lower() and "response" not in content.lower().split("traceback")[1][:50]:
                print_pass("Tracebacks appear to be logged, not returned")
            else:
                print_warn("Check that tracebacks aren't returned in responses")
    
    def check_cors_config(self):
        """Check CORS configuration"""
        print_header("Checking CORS Configuration")
        
        main_py = self.project_root / "backend" / "app" / "main.py"
        
        if not main_py.exists():
            self.warnings.append("main.py not found")
            print_warn("main.py not found")
            return
        
        content = main_py.read_text()
        
        if "CORSMiddleware" in content:
            print_pass("CORS middleware is configured")
            
            # Check for wildcard origins in production
            if 'allow_origins=["*"]' in content.replace(" ", ""):
                self.warnings.append("CORS allows all origins")
                print_warn("CORS allows all origins (*) - restrict in production")
            else:
                print_pass("CORS origins are restricted")
        else:
            self.issues.append("CORS not configured")
            print_fail("CORS middleware not found")
    
    def check_logs_in_gitignore(self):
        """Ensure log files are gitignored"""
        print_header("Checking Logs in .gitignore")
        
        gitignore = self.project_root / ".gitignore"
        if not gitignore.exists():
            return
        
        content = gitignore.read_text()
        
        log_patterns = ["*.log", "logs/", "backend/logs/"]
        found = any(p in content for p in log_patterns)
        
        if found:
            print_pass("Log files are in .gitignore")
        else:
            self.warnings.append("Log files may not be gitignored")
            print_warn("Consider adding *.log or logs/ to .gitignore")
    
    def print_summary(self):
        """Print audit summary"""
        print_header("AUDIT SUMMARY")
        
        total_issues = len(self.issues)
        total_warnings = len(self.warnings)
        
        if total_issues == 0 and total_warnings == 0:
            print(f"{GREEN}All security checks passed!{RESET}")
        else:
            if total_issues > 0:
                print(f"{RED}Issues found: {total_issues}{RESET}")
                for issue in self.issues:
                    print(f"  - {issue}")
            
            if total_warnings > 0:
                print(f"{YELLOW}Warnings: {total_warnings}{RESET}")
                for warning in self.warnings:
                    print(f"  - {warning}")
        
        print()


def main():
    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent  # backend/tests -> root
    
    if not (project_root / "backend").exists():
        # Try current directory
        project_root = Path.cwd()
    
    print(f"Project root: {project_root}")
    
    auditor = SecurityAuditor(project_root)
    success = auditor.run_all_checks()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
