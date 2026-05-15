import sys
import subprocess
import importlib.util

def check_dependencies():
    print("Checking dependencies...")
    dependencies = ["msal", "requests", "dotenv"]
    missing = []
    
    for dep in dependencies:
        if importlib.util.find_spec(dep) is None:
            # Note: 'dotenv' is the module name for 'python-dotenv'
            missing.append(dep)
    
    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        print("Attempting to install from requirements.txt...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("Dependencies installed successfully.\n")
        except Exception as e:
            print(f"Failed to install dependencies: {e}")
            sys.exit(1)
    else:
        print("All dependencies are met.\n")

def run_sync():
    try:
        from sync_goals.main import main
        main()
    except ImportError as e:
        print(f"Error: Could not find the 'sync_goals' package. Ensure you are running from the root directory.")
        print(f"Details: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_dependencies()
    run_sync()
