# Power System Dashboard - Launcher & Scripts

Complete guide for running the Power System Dashboard application and related scripts.

## 📁 File Structure

```
Power-System-py/
├── SYSTEM_ELECTRICAL_PANDAPOWER.py    # Main GUI application
├── routes.py                          # Navigation router (extracted)
├── test_router.py                     # Unit tests for router
├── launcher.py                        # Interactive menu launcher
├── run_all.py                         # Sequential script runner
├── run_launcher.bat                   # Windows batch launcher
├── run_launcher.sh                    # Unix/Linux bash launcher
├── NAVIGATION_README.md               # Navigation architecture docs
└── README.md                          # This file
```

## 🚀 Quick Start

### Option 1: Run Tests Only (Recommended First)
```bash
python run_all.py
```

Output shows all router tests passing:
```
✓ Router initialization test passed
✓ Navigate to results test passed
✓ Navigate to new network test passed
✓ Invalid navigation test passed
✓ Theme toggle test passed
✓ View callbacks test passed
✓ Network callbacks test passed
✓ State queries test passed
✓ Contingency visibility test passed
```

### Option 2: Run Main GUI Application
```bash
python SYSTEM_ELECTRICAL_PANDAPOWER.py
```

Opens the Power System Dashboard with:
- ⚡ Network diagram visualization
- 📊 Power flow analysis
- 🧩 Contingency analysis
- 📈 Results and metrics

### Option 3: Interactive Launcher Menu
```bash
# Windows
run_launcher.bat

# Linux/Mac
bash run_launcher.sh

# Or directly
python launcher.py
```

Choose from:
1. Dashboard application
2. Router tests
3. Run all programs
4. Exit

## 📝 Script Descriptions

### SYSTEM_ELECTRICAL_PANDAPOWER.py
**Main Application**
- Power system analysis dashboard
- Network visualization with Pandapower
- Contingency analysis
- Interactive Plotly charts
- Dark/Light theme toggle
- MVC architecture with Router for navigation

**Dependencies**: PySide6, Pandapower, Plotly, Pandas, Matplotlib

**Run**: `python SYSTEM_ELECTRICAL_PANDAPOWER.py`

---

### test_router.py
**Unit Tests**
- Tests navigation logic without GUI
- 9 comprehensive test cases
- Validates all Router functionality
- No external dependencies required

**Test Coverage**:
- Router initialization
- Navigation between views
- Theme toggling
- Callbacks (view, theme, network)
- State queries
- Contingency visibility

**Run**: `python test_router.py`

---

### run_all.py
**Sequential Script Runner**
- Runs all scripts in defined order
- Perfect for CI/CD pipelines
- Shows summary of results
- Returns exit code based on success

**Run**: `python run_all.py`

**Output Format**:
```
[OK] script_name.py
[FAILED] script_name.py
Total: 1/1 scripts completed successfully
```

---

### launcher.py
**Interactive Program Launcher**
- Menu-driven program selection
- Run individual programs or all
- UTF-8 encoding for proper display
- Keyboard interrupt handling
- Detailed execution feedback

**Features**:
- Check which programs are available
- Run selected program
- Run all programs in sequence
- Go back to menu after each run

**Run**: `python launcher.py`

---

### run_launcher.bat & run_launcher.sh
**Operating System Launchers**

**Windows (run_launcher.bat)**:
- Detects Python installation
- Sets UTF-8 console encoding
- Handles paths with spaces
- Shows execution status
- Returns proper exit codes

```bash
run_launcher.bat
```

**Linux/Mac (run_launcher.sh)**:
- Detects python3 or python
- Handles missing Python gracefully
- Sets proper permissions
- Cross-platform compatible

```bash
bash run_launcher.sh
# or (if made executable)
./run_launcher.sh
```

## 🔧 Configuration

### Adding New Programs to Launcher

Edit `launcher.py` and add to `self.programs` list:

```python
self.programs: List[Tuple[str, str, str]] = [
    ("name", "script.py", "📊 Description"),
    ("new_prog", "new_script.py", "🔧 New Program"),
]
```

Fields:
- **name**: Internal identifier
- **script.py**: Filename to execute
- **Description**: Display in menu

### Python Version
Ensure Python 3.8+ is installed:
```bash
python --version
# or
python3 --version
```

## 📊 Typical Workflow

1. **Test navigation first**:
   ```bash
   python run_all.py
   ```

2. **Run main application**:
   ```bash
   python SYSTEM_ELECTRICAL_PANDAPOWER.py
   ```

3. **Or use interactive launcher**:
   ```bash
   python launcher.py
   ```

## 🐛 Troubleshooting

### "Module not found" errors
Install missing dependencies:
```bash
pip install -r requirements.txt
```

### Encoding errors on Windows
All scripts use UTF-8 encoding explicitly. If issues persist:
```bash
chcp 65001
python launcher.py
```

### Cannot find Python
Ensure Python is in system PATH or use full path:
```bash
C:\Users\YourName\AppData\Local\Programs\Python\Python313\python.exe launcher.py
```

### GUI application won't start
Ensure you have a display server (not running headless):
```bash
# This requires X11/Wayland on Linux or native display on Windows/Mac
python SYSTEM_ELECTRICAL_PANDAPOWER.py
```

### Tests fail with UnicodeEncodeError
Ensure console supports UTF-8:
```bash
# Windows
chcp 65001

# Linux/Mac (usually default)
export LANG=en_US.UTF-8
```

## 📦 Requirements

### Minimal (for tests only)
```
Python >= 3.8
```

### Full (for GUI application)
```
PySide6
pandapower
plotly
pandas
numpy
matplotlib
seaborn
openpyxl  # for Excel export
```

Install all:
```bash
pip install PySide6 pandapower plotly pandas numpy matplotlib seaborn openpyxl
```

## 🔗 Architecture

```
launcher.py (Menu)
    ↓
┌─────────────────────────────┐
│                             │
run_all.py              SYSTEM_ELECTRICAL_PANDAPOWER.py
(automated tests)       (GUI Application)
    ↓                         ↓
test_router.py          PowerSystemController
                              ↓
                         ┌─────┴──────┐
                         │            │
                     router.py   MainWindow
                   (Navigation)   (View)
```

## 📚 Additional Documentation

- **Navigation Architecture**: See `NAVIGATION_README.md`
- **Power Flow Calculations**: See Pandapower documentation
- **PySide6 Styling**: See Qt6 documentation

## 🤝 Contributing

When adding new features:
1. Keep scripts modular
2. Add unit tests (see `test_router.py` as template)
3. Update this README
4. Ensure cross-platform compatibility
5. Test on Windows, Linux, and Mac if possible

## 📄 License

Based on your project's license.

---

**Last Updated**: 2025-12-09  
**Status**: ✅ Fully Functional and Tested
