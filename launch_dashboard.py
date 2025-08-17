#!/usr/bin/env python3
"""
Quick launcher for the Agentic AI Dashboard
"""
import sys
import subprocess
from pathlib import Path

def main():
    """Launch the Streamlit dashboard directly"""
    project_root = Path(__file__).parent
    streamlit_path = project_root / "ui" / "streamlit_app.py"
    
    print("🤖 Launching Agentic AI Dashboard...")
    print("🌐 Opening at: http://localhost:8501")
    print("💡 Use Ctrl+C to stop")
    print("=" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(streamlit_path),
            "--server.port=8501",
            "--server.address=localhost",
            "--browser.gatherUsageStats=false"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()