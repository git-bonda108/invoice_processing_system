#!/usr/bin/env python3
"""
Test runner for Phase 1
"""
import subprocess
import sys
from pathlib import Path

def run_tests():
    """Run Phase 1 tests"""
    project_root = Path(__file__).parent
    test_script = project_root / "test_phase1.py"
    
    try:
        # Run the test script
        result = subprocess.run([sys.executable, str(test_script)], 
                              capture_output=True, text=True, cwd=project_root)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = run_tests()
    if success:
        print("\n🎉 Phase 1 testing completed successfully!")
    else:
        print("\n❌ Phase 1 testing failed!")
    
    sys.exit(0 if success else 1)