import os
import subprocess
import sys
import shutil
import time

def run(cmd, cwd=None):
    print(f"\n🔹 Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f"❌ ERROR: Command failed → {cmd}")
        sys.exit(1)
    print("✅ Done")
    return result

def check_foundry():
    print("\n🔍 Checking for Microsoft Foundry Local...")
    result = shutil.which("foundry")
    if result:
        print("✅ Foundry Local already installed.")
        return True
    else:
        print("⚠️ Foundry Local not found. Installing via winget...")
        run("winget install Microsoft.FoundryLocal")
        return True

def setup_backend():
    print("\n🚀 Setting up backend (Python API)...")
    backend_dir = "backend"

    # Create virtual environment
    if not os.path.exists(os.path.join(backend_dir, "venv")):
        run(f"python -m venv venv", cwd=backend_dir)

    # Activate venv + install
    pip_path = os.path.join(backend_dir, "venv", "Scripts", "pip.exe")
    run(f"{pip_path} install -r requirements.txt", cwd=backend_dir)

def start_backend():
    print("\n▶️ Starting backend server...")
    backend_dir = "backend"
    python_path = os.path.join(backend_dir, "venv", "Scripts", "python.exe")
    run(f"{python_path} app.py", cwd=backend_dir)

def setup_frontend():
    print("\n🚀 Setting up frontend...")
    frontend_dir = "frontend"

    # Install node modules
    if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
        run("npm install", cwd=frontend_dir)

def start_frontend():
    print("\n▶️ Starting frontend...")
    frontend_dir = "frontend"
    run("npm start", cwd=frontend_dir)

def main():
    print("\n====================================")
    print(" 🚀 Foundry Playground Setup Wizard ")
    print("====================================\n")

    check_foundry()
    setup_backend()
    setup_frontend()

    print("\n🎉 All setup completed successfully!")

    print("\nStarting backend + frontend...")

    # Start backend in new terminal
    subprocess.Popen(
        'start cmd /k "cd backend && venv\\Scripts\\python app.py"',
        shell=True
    )

    # Start frontend in new terminal
    subprocess.Popen(
        'start cmd /k "cd frontend && npm start"',
        shell=True
    )

    print("\n🔥 Full system running! Enjoy your Foundry Playground.")
    print("Backend → http://localhost:5000")
    print("Frontend → http://localhost:3000")

if __name__ == "__main__":
    main()
