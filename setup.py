#!/usr/bin/env python3
"""
Setup script for Indian Stock Trading System
Automates the complete installation and configuration process
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

class TradingSystemSetup:
    def __init__(self):
        self.project_name = "indian_trading_system"
        self.base_dir = Path.cwd() / self.project_name
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        
    def print_header(self, title):
        """Print formatted header"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        
    def print_step(self, step, description):
        """Print step information"""
        print(f"\n📋 Step {step}: {description}")
        print("-" * 40)
        
    def run_command(self, command, description=None):
        """Run shell command with error handling"""
        if description:
            print(f"   {description}...")
        
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                check=True, 
                capture_output=True, 
                text=True
            )
            if result.stdout:
                print(f"   ✅ {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Error: {e.stderr.strip()}")
            return False
    
    def create_directory_structure(self):
        """Create the complete directory structure"""
        self.print_step(1, "Creating Directory Structure")
        
        directories = [
            self.base_dir,
            self.base_dir / "config",
            self.base_dir / "src",
            self.base_dir / "src" / "indicators", 
            self.base_dir / "src" / "strategies",
            self.base_dir / "src" / "engines",
            self.base_dir / "src" / "utils",
            self.base_dir / "templates",
            self.base_dir / "static",
            self.base_dir / "static" / "css",
            self.base_dir / "static" / "js",
            self.base_dir / "static" / "images",
            self.base_dir / "logs",
            self.base_dir / "data",
            self.base_dir / "tests"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ Created: {directory.relative_to(Path.cwd())}")
    
    def create_requirements_file(self):
        """Create requirements.txt file"""
        self.print_step(2, "Creating Requirements File")
        
        requirements = """# Core Dependencies
flask==2.3.3
pandas==2.1.0
numpy==1.24.3
requests==2.31.0
python-dotenv==1.0.0

# Technical Analysis
pandas-ta==0.3.14b0

# Data Sources (Reliable for Indian Markets)
nsepy==0.8
nsetools==1.0.11

# Telegram Integration
python-telegram-bot==20.5

# Plotting & Visualization  
plotly==5.16.1
matplotlib==3.7.2

# Async Support
asyncio
aiofiles==23.2.1

# Date/Time Handling
pytz==2023.3

# Development Tools
pytest==7.4.2
black==23.7.0
"""
        
        req_file = self.base_dir / "requirements.txt"
        req_file.write_text(requirements)
        print(f"   ✅ Created: {req_file.relative_to(Path.cwd())}")
    
    def create_env_example(self):
        """Create .env.example file"""
        self.print_step(3, "Creating Environment Configuration")
        
        env_content = """# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Trading Configuration
INITIAL_CAPITAL=100000
MAX_POSITIONS=5
RISK_PER_TRADE=2
PROFIT_TARGET=3000

# Database
DATABASE_URL=sqlite:///trading_system.db

# Flask Configuration
FLASK_DEBUG=True
FLASK_HOST=127.0.0.1
FLASK_PORT=5000

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/trading_system.log

# Market Hours (IST)
MARKET_START_TIME=09:15
MARKET_END_TIME=15:30
"""
        
        env_file = self.base_dir / ".env.example"
        env_file.write_text(env_content)
        print(f"   ✅ Created: {env_file.relative_to(Path.cwd())}")
        
        # Create actual .env file
        env_actual = self.base_dir / ".env"
        if not env_actual.exists():
            env_actual.write_text(env_content)
            print(f"   ✅ Created: {env_actual.relative_to(Path.cwd())}")
    
    def create_gitignore(self):
        """Create .gitignore file"""
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
logs/*.log
*.log

# Database
*.db
*.sqlite3

# OS
.DS_Store
Thumbs.db

# Trading System Specific
data/*.csv
paper_trading.db
trading_system.db
"""
        
        gitignore_file = self.base_dir / ".gitignore"
        gitignore_file.write_text(gitignore_content)
        print(f"   ✅ Created: {gitignore_file.relative_to(Path.cwd())}")
    
    def check_python_version(self):
        """Check Python version compatibility"""
        self.print_step(4, "Checking Python Version")
        
        if sys.version_info < (3, 8):
            print("   ❌ Python 3.8+ is required")
            print(f"   Current version: {self.python_version}")
            return False
        
        print(f"   ✅ Python {self.python_version} is compatible")
        return True
    
    def install_dependencies(self):
        """Install Python dependencies"""
        self.print_step(5, "Installing Dependencies")
        
        os.chdir(self.base_dir)
        
        # Upgrade pip first
        success = self.run_command(
            f"{sys.executable} -m pip install --upgrade pip",
            "Upgrading pip"
        )
        
        if not success:
            return False
        
        # Install dependencies
        success = self.run_command(
            f"{sys.executable} -m pip install -r requirements.txt",
            "Installing required packages"
        )
        
        return success
    
    def create_startup_script(self):
        """Create startup script"""
        self.print_step(6, "Creating Startup Scripts")
        
        # Windows batch file
        batch_content = """@echo off
echo Starting Indian Stock Trading System...
echo.
echo Dashboard will be available at: http://localhost:5000
echo Press Ctrl+C to stop the system
echo.
python main.py
pause
"""
        
        batch_file = self.base_dir / "start.bat"
        batch_file.write_text(batch_content)
        print(f"   ✅ Created: {batch_file.relative_to(Path.cwd())}")
        
        # Unix shell script
        shell_content = """#!/bin/bash
echo "Starting Indian Stock Trading System..."
echo
echo "Dashboard will be available at: http://localhost:5000"
echo "Press Ctrl+C to stop the system"
echo
python3 main.py
"""
        
        shell_file = self.base_dir / "start.sh"
        shell_file.write_text(shell_content)
        
        # Make shell script executable
        if os.name != 'nt':  # Not Windows
            os.chmod(shell_file, 0o755)
        
        print(f"   ✅ Created: {shell_file.relative_to(Path.cwd())}")
    
    def create_readme_template(self):
        """Create a basic README for the generated project"""
        readme_content = """# Indian Stock Trading System

## Quick Start

1. **Configure Telegram** (Optional but recommended):
   - Create a Telegram bot via @BotFather
   - Get your chat ID
   - Update `.env` file with bot token and chat ID

2. **Start the system**:
   ```bash
   # Windows
   start.bat
   
   # Linux/Mac
   ./start.sh
   
   # Or directly
   python main.py
   ```

3. **Access Dashboard**:
   - Open: http://localhost:5000
   - View portfolio, signals, and trade history

## Configuration

Edit `.env` file to customize:
- Capital amount
- Risk per trade
- Telegram settings
- Target profit

## Features

- ✅ Paper trading (no real money)
- ✅ Technical analysis signals
- ✅ Web dashboard
- ✅ Telegram alerts
- ✅ Backtesting
- ✅ Market regime detection

## Support

For issues and documentation, check the main README file.
"""
        
        readme_file = self.base_dir / "README.md"
        readme_file.write_text(readme_content)
        print(f"   ✅ Created: {readme_file.relative_to(Path.cwd())}")
    
    def display_completion_message(self):
        """Display completion message with next steps"""
        self.print_header("🎉 Setup Complete!")
        
        print(f"""
The Indian Stock Trading System has been successfully set up!

📁 Project Location: {self.base_dir}

🚀 Next Steps:

1. **Navigate to project directory**:
   cd {self.project_name}

2. **Copy all the Python files** from the artifacts to respective directories:
   - main.py (root directory)
   - config/settings.py
   - src/*.py files
   - templates/*.html files  
   - static/css/style.css
   - static/js/dashboard.js

3. **Configure Telegram Bot** (Optional):
   - Create bot via @BotFather on Telegram
   - Update .env file with your bot token and chat ID

4. **Start the system**:
   # Windows: double-click start.bat
   # Linux/Mac: ./start.sh
   # Or: python main.py

5. **Access Dashboard**:
   Open http://localhost:5000 in your browser

📊 **System Features**:
✅ Paper trading (no real money at risk)
✅ Technical analysis with multiple indicators
✅ Market regime detection (Bull/Bear/Sideways)
✅ Real-time Telegram alerts
✅ Web dashboard with live updates
✅ Backtesting engine
✅ Trade history and performance analytics

🎯 **Daily Target**: ₹3,000 profit through automated trading signals

⚠️  **Important**: This is a paper trading system for educational purposes.
    Always test thoroughly before considering real money trading.

📚 **Documentation**: Check README.md for detailed information.

Happy Trading! 📈
""")

def main():
    """Main setup function"""
    print("🚀 Indian Stock Trading System - Automated Setup")
    print("=" * 60)
    print("This script will set up the complete trading system structure.")
    print("Make sure you have Python 3.8+ installed.")
    
    # Ask for confirmation
    response = input("\nDo you want to proceed with the setup? (y/N): ").strip().lower()
    
    if response not in ['y', 'yes']:
        print("Setup cancelled.")
        return
    
    setup = TradingSystemSetup()
    
    try:
        # Check Python version
        if not setup.check_python_version():
            return
        
        # Create directory structure
        setup.create_directory_structure()
        
        # Create configuration files
        setup.create_requirements_file()
        setup.create_env_example()
        setup.create_gitignore()
        
        # Create utility scripts
        setup.create_startup_script()
        setup.create_readme_template()
        
        # Install dependencies
        install_deps = input("\nInstall Python dependencies now? (Y/n): ").strip().lower()
        if install_deps not in ['n', 'no']:
            if not setup.install_dependencies():
                print("\n⚠️ Dependency installation failed. You can install manually later:")
                print(f"   cd {setup.project_name}")
                print("   pip install -r requirements.txt")
        
        # Display completion message
        setup.display_completion_message()
        
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user.")
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        print("Please try running the setup again or install manually.")

if __name__ == "__main__":
    main()