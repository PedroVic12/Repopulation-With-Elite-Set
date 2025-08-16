# Framework Documentation

## Overview
Evolutionary algorithm framework for power system contingency analysis using PandaPower and DEAP.

## Core Components
1. **Genetic Algorithm Engine**
   - Population management
   - Selection, crossover, mutation
   - Elite preservation

2. **PandaPower Integration**
   - IEEE 14-bus system modeling
   - Contingency simulation
   - Power flow analysis

3. **Launcher Interface**
   - Parameter configuration
   - Execution control
   - Results visualization

## Setup
1. **Prerequisites**
   - Python 3.8+
   - Dependencies: `pip install -r requirements.txt`
   - PandaPower: `pip install pandapower`

2. **Configuration**
   - `params.json`: Main configuration
   - `options.json`: Variable parameters

## Usage
1. **Basic Execution**
   ```bash
   python launcher.py
   ```

2. **Key Features**
   - Elite preservation
   - Custom fitness functions
   - Batch execution support
   - Real-time monitoring

## Contingency Analysis
- N-1 contingency simulation
- Voltage stability assessment
- Line loading analysis
- Generator reactive power limits

## Troubleshooting
- **Power flow divergence**: Check system parameters
- **Performance issues**: Reduce population size
- **Installation problems**: Verify Python version and dependencies
