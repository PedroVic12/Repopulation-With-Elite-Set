"""
run_all.py - Simple Script Runner

Runs all scripts sequentially without interactive menu.
Perfect for CI/CD pipelines or automated testing.
"""

import sys
import subprocess
from pathlib import Path


def run_script(filepath: Path) -> bool:
    """Run a single Python script."""
    print(f"\n{'='*70}")
    print(f"Running: {filepath.name}")
    print('='*70)
    
    try:
        result = subprocess.run(
            [sys.executable, str(filepath)],
            cwd=filepath.parent,
            check=False
        )
        return result.returncode == 0
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def main():
    """Run all Python scripts in the directory."""
    script_dir = Path(__file__).parent
    
    # Scripts to run (in order)
    scripts = [
        script_dir / "test_router.py",
        # Uncomment to run the GUI app (requires display):
        # script_dir / "SYSTEM_ELECTRICAL_PANDAPOWER.py",
    ]
    
    print("\n" + "="*70)
    print("Running All Scripts")
    print("="*70)
    
    results = []
    for script in scripts:
        if script.exists():
            success = run_script(script)
            results.append((script.name, success))
        else:
            print(f"\nWARNING: Script not found: {script.name}")
            results.append((script.name, False))
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    for name, success in results:
        status = "[OK]" if success else "[FAILED]"
        print(f"{status} {name}")
    
    total = len(results)
    successful = sum(1 for _, s in results if s)
    print(f"\nTotal: {successful}/{total} scripts completed successfully")
    print("="*70 + "\n")
    
    return 0 if successful == total else 1


if __name__ == "__main__":
    sys.exit(main())
