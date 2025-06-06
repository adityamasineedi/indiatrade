# startup_diagnostic.py - Run this first to identify issues
"""
Quick diagnostic script to identify and fix common issues
Run this before starting main.py
"""

import os
import sys
import importlib
from datetime import datetime

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"🐍 Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    
    print("✅ Python version OK")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'flask', 'pandas', 'numpy', 'requests', 'python-dotenv'
    ]
    
    optional_packages = [
        'nsepy', 'yfinance', 'plotly', 'matplotlib'
    ]
    
    missing_required = []
    missing_optional = []
    
    print("\n📦 Checking Dependencies...")
    
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_required.append(package)
            print(f"❌ {package} - REQUIRED")
    
    for package in optional_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_optional.append(package)
            print(f"⚠️ {package} - optional")
    
    if missing_required:
        print(f"\n🚨 Install required packages:")
        print(f"pip install {' '.join(missing_required)}")
        return False
    
    if missing_optional:
        print(f"\n💡 Recommended packages:")
        print(f"pip install {' '.join(missing_optional)}")
    
    return True

def check_file_structure():
    """Check if required files exist"""
    required_files = [
        'main.py',
        'config/settings.py',
        'src/data_fetcher.py',
        'templates/dashboard.html',
        'templates/base.html'
    ]
    
    print("\n📁 Checking File Structure...")
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path}")
    
    if missing_files:
        print(f"\n🚨 Missing files detected!")
        print("Make sure you have all the code files in the correct locations")
        return False
    
    return True

def check_environment():
    """Check environment configuration"""
    print("\n⚙️ Checking Environment...")
    
    if os.path.exists('.env'):
        print("✅ .env file exists")
    else:
        if os.path.exists('.env.example'):
            print("⚠️ .env missing, .env.example found")
            print("Run: cp .env.example .env")
        else:
            print("❌ No environment files found")
            return False
    
    return True

def test_imports():
    """Test critical imports"""
    print("\n🧪 Testing Imports...")
    
    # Add src to path
    src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    tests = [
        ('flask', 'Flask'),
        ('pandas', 'pandas'),
        ('datetime', 'datetime'),
        ('data_fetcher', 'DataFetcher'),
        ('config.settings', 'Config')
    ]
    
    failed_imports = []
    
    for module, component in tests:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError as e:
            failed_imports.append((module, str(e)))
            print(f"❌ {module}: {e}")
    
    if failed_imports:
        print(f"\n🚨 Import failures detected!")
        for module, error in failed_imports:
            print(f"  {module}: {error}")
        return False
    
    return True

def run_flask_test():
    """Test Flask app creation"""
    print("\n🌐 Testing Flask App...")
    
    try:
        from flask import Flask
        app = Flask(__name__)
        
        @app.route('/test')
        def test():
            return {'status': 'working', 'timestamp': datetime.now().isoformat()}
        
        print("✅ Flask app creation successful")
        return True
    except Exception as e:
        print(f"❌ Flask test failed: {e}")
        return False

def generate_fixes():
    """Generate fix commands"""
    print("\n🔧 QUICK FIXES:")
    print("================")
    
    print("\n1. Install dependencies:")
    print("pip install flask pandas numpy requests python-dotenv nsepy yfinance")
    
    print("\n2. Setup environment:")
    print("cp .env.example .env")
    
    print("\n3. Create missing directories:")
    print("mkdir -p logs data")
    
    print("\n4. Test the system:")
    print("python main.py")
    
    print("\n5. Access dashboard:")
    print("http://localhost:5000")

def main():
    """Run all diagnostics"""
    print("🚀 TRADING SYSTEM STARTUP DIAGNOSTIC")
    print("=" * 40)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("File Structure", check_file_structure),
        ("Environment", check_environment),
        ("Imports", test_imports),
        ("Flask Test", run_flask_test)
    ]
    
    results = {}
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
            if not results[check_name]:
                all_passed = False
        except Exception as e:
            print(f"❌ {check_name} failed with error: {e}")
            results[check_name] = False
            all_passed = False
    
    print("\n" + "=" * 40)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 40)
    
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check_name}: {status}")
    
    if all_passed:
        print("\n🎉 ALL CHECKS PASSED!")
        print("Your system is ready to run!")
        print("\nNext step: python main.py")
    else:
        print("\n⚠️ ISSUES FOUND")
        print("Fix the failed checks above, then run:")
        print("python startup_diagnostic.py")
        generate_fixes()
    
    return all_passed

if __name__ == "__main__":
    main()