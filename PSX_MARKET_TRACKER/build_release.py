import os
import subprocess
import sys
import shutil

def build():
    print("🚀 Starting Production Build for PSX Market Tracker...")
    
    # 1. Cleanup old build artifacts
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            print(f"🧹 Removing {folder}...")
            shutil.rmtree(folder)
            
    for f in os.listdir('.'):
        if f.endswith('.spec'):
            print(f"🧹 Removing {f}...")
            os.remove(f)

    # 2. Determine paths
    venv_python = os.path.join("venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        venv_python = sys.executable # Fallback
        
    main_script = "run.py"
    icon_path = os.path.join("assets", "icon.ico")
    
    # 3. Construct PyInstaller command
    # --noconfirm: Overwrite output directory
    # --onefile: Create a single executable
    # --windowed: No console window
    # --name: Executable name
    # --icon: App icon
    # --add-data: Bundle assets and legal folders
    
    cmd = [
        venv_python, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "PSX_Market_Tracker",
        "--icon", icon_path,
        "--add-data", f"assets{os.pathsep}assets",
        "--add-data", f"legal{os.pathsep}legal",
        "--hidden-import", "xlsxwriter",
        "--hidden-import", "fpdf",
        main_script
    ]
    
    print(f"🛠️  Running Build Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Build Successful!")
        print(f"📁 Executable located in: {os.path.abspath('dist')}")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build()
