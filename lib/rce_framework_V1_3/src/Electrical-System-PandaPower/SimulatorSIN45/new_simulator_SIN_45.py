import sys
import os
import webbrowser
import re
import traceback
import base64
import logging
import json
import copy
from io import BytesIO, StringIO
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import pandapower as pp
import pandapower.plotting as plot
from pandapower.auxiliary import LoadflowNotConverged
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.gridspec as gridspec
import numpy as np
from matplotlib.lines import Line2D
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Define o backend Qt para o Matplotlib
os.environ['QT_API'] = 'PySide6'

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QFileDialog,
    QMessageBox, QHeaderView, QGroupBox, QSplitter, QLabel, QScrollArea,
    QProgressBar, QTextEdit, QComboBox, QSpinBox, QCheckBox, QDialog,
    QDialogButtonBox, QFormLayout, QDoubleSpinBox, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QThread, QTimer, Signal, QObject
from PySide6.QtGui import QFont, QPixmap, QIcon, QTextCursor
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

# =============================================================================
# CONFIGURAÇÕES E LOGGING
# =============================================================================

@dataclass
class SimulationConfig:
    """Centraliza configurações do simulador"""
    max_iterations: int = 30
    tolerance: float = 1e-6
    enforce_q_limits: bool = True
    algorithm: str = 'nr'  # newton-raphson
    voltage_limits: Dict[str, float] = None
    thermal_limits_check: bool = True
    numba_acceleration: bool = True

    def __post_init__(self):
        if self.voltage_limits is None:
            self.voltage_limits = {'min': 0.95, 'max': 1.05}

    def save_to_file(self, filepath: str):
        """Salva configurações em arquivo JSON"""
        with open(filepath, 'w') as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str):
        """Carrega configurações de arquivo JSON"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return cls(**data)
        except:
            return cls()  # Retorna config padrão se falhar

def setup_logging():
    """Configura o sistema de logging para a GUI, removendo handlers de console/arquivo."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    # Limpa handlers existentes para evitar logs duplicados ou no console
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    return logging.getLogger(__name__)  # Retorna o logger específico da aplicação

# =============================================================================
# VALIDAÇÃO ROBUSTA DE DADOS
# =============================================================================

class DataValidator:
    """Validador robusto para dados de entrada"""

    @staticmethod
    def validate_bus_data(df_bus: pd.DataFrame) -> Tuple[bool, List[str]]:
        errors = []
        if df_bus.empty:
            errors.append("DataFrame de barras está vazio")
            return False, errors

        required_cols = ['bus_id', 'name']
        missing_cols = [col for col in required_cols if col not in df_bus.columns]
        if missing_cols:
            errors.append(f"Colunas obrigatórias ausentes: {missing_cols}")

        if 'bus_id' in df_bus.columns and df_bus['bus_id'].duplicated().any():
            duplicates = df_bus[df_bus['bus_id'].duplicated()]['bus_id'].tolist()
            errors.append(f"IDs de barra duplicados: {duplicates}")

        if 'vn_kv' in df_bus.columns:
            invalid_vn = df_bus[(df_bus['vn_kv'] <= 0) | (df_bus['vn_kv'] > 1000)]
            if not invalid_vn.empty:
                errors.append(f"Tensões nominais inválidas nas barras: {invalid_vn['bus_id'].tolist()}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_line_data(df_line: pd.DataFrame, valid_buses: set) -> Tuple[bool, List[str]]:
        errors = []
        if df_line.empty:
            return True, []  # OK se não houver linhas

        if 'from_bus' in df_line.columns and 'to_bus' in df_line.columns:
            # Ensure bus columns are numeric before comparison
            from_buses_numeric = pd.to_numeric(df_line['from_bus'], errors='coerce').dropna()
            to_buses_numeric = pd.to_numeric(df_line['to_bus'], errors='coerce').dropna()
            
            invalid_from = set(from_buses_numeric) - valid_buses
            invalid_to = set(to_buses_numeric) - valid_buses
            if invalid_from:
                errors.append(f"Barras 'from_bus' inexistentes: {invalid_from}")
            if invalid_to:
                errors.append(f"Barras 'to_bus' inexistentes: {invalid_to}")

        impedance_cols = ['x_pu', 'r_pu']
        for col in impedance_cols:
            if col in df_line.columns:
                numeric_col = pd.to_numeric(df_line[col], errors='coerce')
                negative_values = numeric_col[numeric_col < 0]
                if not negative_values.empty:
                    errors.append(f"Valores negativos em {col}")

        return len(errors) == 0, errors

# =============================================================================
# ANÁLISE DE CONTINGÊNCIAS
# =============================================================================

class ContingencyAnalyzer:
    """Análise N-1 e N-2 para estudos de contingência"""

    def __init__(self, net, config: SimulationConfig):
        self.net = net
        self.config = config
        self.base_results = None
        self.logger = logging.getLogger(__name__)

    def run_n_minus_1_analysis(self) -> Dict[str, Any]:
        """Executa análise N-1 para todas as linhas"""
        if self.net.line.empty and self.net.trafo.empty:
            return {}

        try:
            pp.runpp(self.net, algorithm=self.config.algorithm,
                      max_iteration=self.config.max_iterations,
                      enforce_q_lims=self.config.enforce_q_limits,
                      numba=self.config.numba_acceleration)
            if not self.net.converged:
                return {'error': 'Caso base não convergiu'}
            self.base_results = {
                'bus_voltages': self.net.res_bus.vm_pu.copy(),
                'line_loading': self.net.res_line.loading_percent.copy() if not self.net.res_line.empty else pd.Series(),
                'trafo_loading': self.net.res_trafo.loading_percent.copy() if not self.net.res_trafo.empty else pd.Series()
            }
        except Exception as e:
            return {'error': f'Erro no caso base: {str(e)}'}

        contingency_results = {}
        elements_to_run = [('line', idx) for idx in self.net.line.index] + \
                          [('trafo', idx) for idx in self.net.trafo.index]
        
        total_elements = len(elements_to_run)
        self.logger.info(f"Iniciando análise N-1 para {total_elements} elementos (linhas/trafos)")

        for i, (elem_type, elem_idx) in enumerate(elements_to_run):
            element_df = getattr(self.net, elem_type)
            original_service = element_df.at[elem_idx, 'in_service']
            element_df.at[elem_idx, 'in_service'] = False
            
            try:
                pp.runpp(self.net, algorithm=self.config.algorithm,
                          max_iteration=self.config.max_iterations,
                          enforce_q_lims=self.config.enforce_q_limits,
                          numba=self.config.numba_acceleration)
                
                contingency_name = f'{elem_type}_{elem_idx}'
                if self.net.converged:
                    violations = self._check_violations()
                    severity = self._calculate_severity(violations)
                    max_loading = 0.0
                    if not self.net.res_line.empty and 'loading_percent' in self.net.res_line:
                        max_loading = max(max_loading, float(self.net.res_line.loading_percent.max()))
                    if not self.net.res_trafo.empty and 'loading_percent' in self.net.res_trafo:
                        max_loading = max(max_loading, float(self.net.res_trafo.loading_percent.max()))
                    
                    contingency_results[contingency_name] = {
                        'converged': True, 'violations': violations or ['OK'], 'severity': severity,
                        'max_voltage': float(self.net.res_bus.vm_pu.max()),
                        'min_voltage': float(self.net.res_bus.vm_pu.min()),
                        'max_loading': max_loading
                    }
                else:
                    contingency_results[contingency_name] = {
                        'converged': False, 'violations': ['Não convergiu'], 'severity': 'CRITICAL'
                    }
            except Exception as e:
                contingency_results[contingency_name] = {
                    'converged': False, 'violations': [f'Erro na simulação: {str(e)}'], 'severity': 'CRITICAL'
                }
            finally:
                element_df.at[elem_idx, 'in_service'] = original_service

            if (i + 1) % 10 == 0:
                self.logger.info(f"Progresso N-1: {i+1}/{total_elements} elementos analisados")
                
        return contingency_results


    def _check_violations(self) -> List[str]:
        """Verifica violações de tensão e carregamento"""
        violations = []
        low_voltage = self.net.res_bus[self.net.res_bus.vm_pu < self.config.voltage_limits['min']]
        high_voltage = self.net.res_bus[self.net.res_bus.vm_pu > self.config.voltage_limits['max']]
        if not low_voltage.empty:
            violations.append(f"Tensão baixa em {len(low_voltage)} barras (min: {low_voltage.vm_pu.min():.3f} pu)")
        if not high_voltage.empty:
            violations.append(f"Tensão alta em {len(high_voltage)} barras (max: {high_voltage.vm_pu.max():.3f} pu)")
        if not self.net.res_line.empty and 'loading_percent' in self.net.res_line:
            overloaded = self.net.res_line[self.net.res_line.loading_percent > 100]
            if not overloaded.empty:
                violations.append(f"Sobrecarga em {len(overloaded)} linhas (max: {overloaded.loading_percent.max():.1f}%)")
        if not self.net.res_trafo.empty and 'loading_percent' in self.net.res_trafo:
            overloaded_trafo = self.net.res_trafo[self.net.res_trafo.loading_percent > 100]
            if not overloaded_trafo.empty:
                violations.append(f"Sobrecarga em {len(overloaded_trafo)} trafos (max: {overloaded_trafo.loading_percent.max():.1f}%)")
        return violations

    def _calculate_severity(self, violations: List[str]) -> str:
        """Calcula severidade das violações"""
        if not violations: return 'OK'
        elif len(violations) <= 2: return 'WARNING'
        else: return 'CRITICAL'

# =============================================================================
# ANÁLISE ESTATÍSTICA AVANÇADA
# =============================================================================

class StatisticalAnalyzer:
    """Análises estatísticas dos resultados"""

    @staticmethod
    def voltage_stability_analysis(net) -> Dict[str, Any]:
        """Análise de estabilidade de tensão"""
        if net.res_bus.empty: return {}
        voltages = net.res_bus.vm_pu
        return {
            'voltage_statistics': {
                'mean': float(voltages.mean()), 'std': float(voltages.std()),
                'min': float(voltages.min()), 'max': float(voltages.max()),
                'cv': float(voltages.std() / voltages.mean()) if voltages.mean() > 0 else 0
            },
            'voltage_distribution': {
                'below_0_95': int((voltages < 0.95).sum()),
                'normal_range': int(((voltages >= 0.95) & (voltages <= 1.05)).sum()),
                'above_1_05': int((voltages > 1.05).sum())
            },
            'critical_buses': voltages[(voltages < 0.90) | (voltages > 1.10)].index.tolist()
        }

    @staticmethod
    def loading_analysis(net) -> Dict[str, Any]:
        """Análise de carregamento das linhas"""
        if net.res_line.empty: return {}
        loading = net.res_line.loading_percent
        return {
            'loading_statistics': {
                'mean': float(loading.mean()), 'std': float(loading.std()),
                'max': float(loading.max()), 'percentile_95': float(loading.quantile(0.95))
            },
            'loading_distribution': {
                'light_load': int((loading < 30).sum()),
                'medium_load': int(((loading >= 30) & (loading < 70)).sum()),
                'heavy_load': int(((loading >= 70) & (loading < 100)).sum()),
                'overload': int((loading >= 100).sum())
            },
            'critical_lines': loading[loading > 90].index.tolist()
        }

# =============================================================================
# SISTEMA DE ALERTAS INTELIGENTE
# =============================================================================

class AlertSystem:
    """Sistema inteligente de alertas e recomendações"""

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.alerts = []

    def analyze_network_health(self, net) -> Dict[str, Any]:
        """Análise completa da saúde da rede"""
        if not net.converged:
            return {
                'status': 'CRITICAL', 'message': 'Rede não convergiu',
                'voltage_issues': [], 'loading_issues': [],
                'recommendations': ['Verificar dados de entrada e topologia da rede']
            }
        voltage_issues = self._check_voltage_issues(net)
        loading_issues = self._check_loading_issues(net)
        stability_issues = self._check_stability_issues(net)
        total_issues = len(voltage_issues) + len(loading_issues) + len(stability_issues)
        if total_issues == 0:
            status, message = 'HEALTHY', 'Rede operando dentro dos limites normais'
        elif total_issues <= 3:
            status, message = 'WARNING', f'{total_issues} problemas detectados - atenção necessária'
        else:
            status, message = 'CRITICAL', f'{total_issues} problemas graves detectados - ação imediata necessária'
        return {
            'status': status, 'message': message, 'voltage_issues': voltage_issues,
            'loading_issues': loading_issues, 'stability_issues': stability_issues,
            'recommendations': self._generate_recommendations(net, voltage_issues, loading_issues)
        }

    def _check_voltage_issues(self, net) -> List[str]:
        issues = []
        if net.res_bus.empty: return issues
        voltages = net.res_bus.vm_pu
        low_voltage_buses = voltages[voltages < self.config.voltage_limits['min']]
        high_voltage_buses = voltages[voltages > self.config.voltage_limits['max']]
        if not low_voltage_buses.empty:
            issues.append(f"Tensão baixa em {len(low_voltage_buses)} barras (mín: {low_voltage_buses.min():.3f} pu)")
        if not high_voltage_buses.empty:
            issues.append(f"Tensão alta em {len(high_voltage_buses)} barras (máx: {high_voltage_buses.max():.3f} pu)")
        return issues

    def _check_loading_issues(self, net) -> List[str]:
        issues = []
        if net.res_line.empty and net.res_trafo.empty: return issues
        
        if not net.res_line.empty and 'loading_percent' in net.res_line:
            loading = net.res_line.loading_percent
            overloaded = loading[loading > 100]
            heavily_loaded = loading[(loading > 80) & (loading <= 100)]
            if not overloaded.empty:
                issues.append(f"Sobrecarga em {len(overloaded)} linhas (máx: {overloaded.max():.1f}%)")
            if not heavily_loaded.empty:
                issues.append(f"Carregamento alto em {len(heavily_loaded)} linhas (>80%)")
        
        if not net.res_trafo.empty and 'loading_percent' in net.res_trafo:
            loading_trafo = net.res_trafo.loading_percent
            overloaded_trafo = loading_trafo[loading_trafo > 100]
            heavily_loaded_trafo = loading_trafo[(loading_trafo > 80) & (loading_trafo <= 100)]
            if not overloaded_trafo.empty:
                issues.append(f"Sobrecarga em {len(overloaded_trafo)} trafos (máx: {overloaded_trafo.max():.1f}%)")
            if not heavily_loaded_trafo.empty:
                issues.append(f"Carregamento alto em {len(heavily_loaded_trafo)} trafos (>80%)")

        return issues

    def _check_stability_issues(self, net) -> List[str]:
        issues = []
        if net.res_bus.empty: return issues
        voltages = net.res_bus.vm_pu
        voltage_spread = voltages.max() - voltages.min()
        if voltage_spread > 0.15:
            issues.append(f"Grande variação de tensão na rede ({voltage_spread:.3f} pu)")
        return issues

    def _generate_recommendations(self, net, voltage_issues, loading_issues) -> List[str]:
        recommendations = []
        if voltage_issues:
            if any('baixa' in issue for issue in voltage_issues):
                recommendations.append("Considere instalar compensação reativa ou ajustar taps de transformadores")
            if any('alta' in issue for issue in voltage_issues):
                recommendations.append("Verifique geradores e sistemas de excitação")
        if loading_issues:
            if any('Sobrecarga' in issue for issue in loading_issues):
                recommendations.append("Linhas/Trafos sobrecarregados - considere reforços ou redespacho")
            if any('alto' in issue for issue in loading_issues):
                recommendations.append("Monitore elementos com carregamento elevado")
        if not recommendations:
            recommendations.append("Rede operando dentro dos parâmetros normais")
        return recommendations

# =============================================================================
# ESTILOS DA APLICAÇÃO
# =============================================================================

AppStyles = """
QWidget {
    background-color: #2E2E2E;
    color: #F0F0F0;
    font-family: "Segoe UI";
}
QMainWindow, QGroupBox { background-color: #2E2E2E; }
QGroupBox {
    font-weight: bold; border: 1px solid #555; border-radius: 5px;
    margin-top: 10px; padding: 15px;
}
QGroupBox::title {
    subcontrol-origin: margin; subcontrol-position: top center;
    padding: 0 10px; color: #F0F0F0;
}
QPushButton {
    border-radius: 4px; padding: 8px; color: white;
    font-weight: bold; border: 1px solid #555;
}
QPushButton#run_button, QPushButton#build_button, QPushButton#contingency_button {
    background-color: #8A2BE2; /* Roxo */
}
QPushButton#run_button:hover, QPushButton#build_button:hover, QPushButton#contingency_button:hover {
    background-color: #9932CC;
}
QPushButton { background-color: #2E8B57; } /* Verde */
QPushButton:hover { background-color: #3CB371; }
QTabWidget::pane { border-top: 2px solid #555; }
QTabBar::tab {
    background: #444; border: 1px solid #555; padding: 8px 16px; color: #F0F0F0;
}
QTabBar::tab:selected { background: #8A2BE2; color: white; }
QTableWidget {
    gridline-color: #555; background-color: #3C3C3C;
    color: #F0F0F0; alternate-background-color: #454545;
}
QHeaderView::section {
    background-color: #555; padding: 4px; border: 1px solid #666; color: #F0F0F0;
}
QProgressBar {
    border: 1px solid #555; border-radius: 5px;
    text-align: center; color: #F0F0F0;
}
QProgressBar::chunk { background-color: #8A2BE2; border-radius: 5px; }
QTextEdit, QListWidget, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #3C3C3C; border: 1px solid #555;
    border-radius: 5px; padding: 5px;
}
QListWidget::item { padding: 5px; border-bottom: 1px solid #555; }
QListWidget::item:selected { background-color: #8A2BE2; }
"""

# =============================================================================
# PARSER DE ARQUIVOS ANAREDE
# =============================================================================
class AnaredeParser:
    @staticmethod
    def parse_pwf_to_dataframes(filepath):
        data_blocks = {'DBAR': [], 'DLIN': [], 'DGER': [], 'DCAR': [], 'DBSH': [], 'DTRA': []}
        current_block = None
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith(('(', '99999')):
                        if line.startswith('99999'): current_block = None
                        continue
                    block_match = re.match(r'^(\w{4})', line)
                    if block_match and block_match.group(1).upper() in data_blocks:
                        current_block = block_match.group(1).upper()
                        continue
                    if current_block: data_blocks[current_block].append(line)
        except Exception as e:
            raise IOError(f"Erro ao ler o ficheiro {filepath}: {e}")

        dfs, bus_vn_kv_map = {}, {}
        if data_blocks['DBAR']:
            bus_data = []
            for line in data_blocks['DBAR']:
                try:
                    num_barra, nome_barra, vn_kv = int(line[0:5]), line[10:22].strip(), float(line[28:34])
                    bus_data.append({'bus_id': num_barra, 'name': nome_barra, 'vn_kv': vn_kv})
                    bus_vn_kv_map[num_barra] = vn_kv
                except (ValueError, IndexError): continue
            dfs['bus'] = pd.DataFrame(bus_data)
        if data_blocks['DLIN']:
            line_data, sn_mva = [], 100.0
            for line in data_blocks['DLIN']:
                try:
                    de, para, r_pu, x_pu, b_pu = int(line[0:5]), int(line[6:11]), float(line[21:29]), float(line[30:38]), float(line[39:47])
                    vn_kv = bus_vn_kv_map.get(de, 230.0)
                    z_base = (vn_kv**2) / sn_mva if vn_kv > 0 else 0
                    r_ohm, x_ohm = r_pu * z_base, x_pu * z_base
                    c_nf = (b_pu / (2 * np.pi * 60 * z_base)) * 1e9 if z_base > 0 else 0
                    line_data.append({'from_bus': de, 'to_bus': para, 'length_km': 1.0, 'r_ohm_per_km': r_ohm, 'x_ohm_per_km': x_ohm, 'c_nf_per_km': c_nf, 'max_i_ka': 1.0, 'r_pu':r_pu, 'x_pu': x_pu, 'b_pu':b_pu})
                except (ValueError, IndexError): continue
            dfs['line'] = pd.DataFrame(line_data)
        return dfs

# =============================================================================
# MODELO DO SISTEMA DE POTÊNCIA
# =============================================================================
class PowerSystemModel:
    def __init__(self, config: SimulationConfig = None):
        self.net = pp.create_empty_network()
        self.dataframes = {}
        self.config = config or SimulationConfig()
        self.validator = DataValidator()
        self.logger = logging.getLogger(__name__)

    def load_data_from_excel(self, filepath):
        try:
            xls = pd.ExcelFile(filepath)
            self.dataframes = {sheet_name: pd.read_excel(xls, sheet_name) for sheet_name in xls.sheet_names}
            # The standardization will be called before building the network
            return self.dataframes
        except Exception as e:
            raise ValueError(f"Não foi possível ler o ficheiro Excel: {e}")

    def _validate_all_data(self) -> Dict[str, Any]:
        all_errors = []
        if 'bus' in self.dataframes:
            is_valid, errors = self.validator.validate_bus_data(self.dataframes['bus'])
            if not is_valid: all_errors.extend([f"Bus: {error}" for error in errors])
        
        if 'line' in self.dataframes and 'bus' in self.dataframes:
            valid_buses = set(pd.to_numeric(self.dataframes['bus']['bus_id'], errors='coerce').dropna())
            is_valid, errors = self.validator.validate_line_data(self.dataframes['line'], valid_buses)
            if not is_valid: all_errors.extend([f"Line: {error}" for error in errors])
            
        return {'is_valid': len(all_errors) == 0, 'errors': all_errors}

    def _standardize_columns(self):
        """Standardizes column names across all loaded dataframes to handle variations."""
        
        mappings = {
            # Standard Name : [Possible Variations in Lower Case]
            'bus_id': ['barra', 'bus_id', 'id', 'numero', 'nº', 'n.º', 'número da barra', 'nº da barra'],
            'name': ['nome', 'name', 'descrição', 'descricao'],
            'vn_kv': ['vn_kv', 'tensao', 'tensão', 'tensao_kv', 'tensão nominal (kv)', 'vn (kv)'],
            'from_bus': ['de', 'from_bus', 'from', 'barra de', 'de_barra'],
            'to_bus': ['para', 'to_bus', 'to', 'barra para', 'para_barra'],
            'r_pu': ['r(pu)', 'r_pu', 'resistencia', 'resistência (pu)', 'r pu'],
            'x_pu': ['x(pu)', 'x_pu', 'reatancia', 'reatância (pu)', 'x pu'],
            'b_pu': ['b(pu)', 'b_pu', 'susceptancia', 'susceptância (pu)', 'b pu'],
            'sn_mva': ['sn_mva', 'potência aparente (mva)', 'sn (mva)'],
            'p_mw': ['p_mw', 'potência ativa (mw)', 'carga ativa (mw)', 'potencia ativa (mw)', 'p (mw)', 'geracao mw', 'geração mw'],
            'q_mvar': ['q_mvar', 'potência reativa (mvar)', 'carga reativa (mvar)', 'potencia reativa (mvar)', 'q (mvar)'],
        }

        for df_name in self.dataframes:
            if isinstance(self.dataframes[df_name], pd.DataFrame):
                df = self.dataframes[df_name]
                rename_dict = {}
                original_cols = {str(col).lower().strip(): col for col in df.columns}
                
                for standard_name, variations in mappings.items():
                    if standard_name in rename_dict.values(): continue
                    for var in variations:
                        if var in original_cols:
                            original_col_name = original_cols[var]
                            if original_col_name not in rename_dict:
                                rename_dict[original_col_name] = standard_name
                                break
                
                if rename_dict:
                    df.rename(columns=rename_dict, inplace=True)

    def create_network_from_dataframes(self):
        if not self.dataframes: raise ValueError("Nenhum dado carregado para criar a rede.")
        
        self._standardize_columns()

        validation_results = self._validate_all_data()
        if not validation_results['is_valid']:
            self.logger.error(f"Dados inválidos: {validation_results['errors']}")
            raise ValueError(f"Dados inválidos detectados: {validation_results['errors']}")

        self.net = pp.create_empty_network(sn_mva=100)
        bus_map, bus_vn_map = {}, {}
        
        if 'bus' not in self.dataframes: raise ValueError("Aba 'bus' (ou similar) em falta no arquivo.")
        df_bus = self.dataframes['bus']
        
        if 'bus_id' not in df_bus.columns:
            raise ValueError("Coluna de ID da barra ('bus_id', 'Barra', etc.) não encontrada na aba 'bus'.")
        if 'name' not in df_bus.columns:
            raise ValueError("Coluna de nome da barra ('name', 'Nome', etc.) não encontrada na aba 'bus'.")

        if 'vn_kv' not in df_bus.columns:
            def extract_vn(name):
                try:
                    match = re.search(r'[\._ ]([\d\.]+)$', str(name))
                    if match: return float(match.group(1))
                except (ValueError, TypeError): pass
                return 230.0 # Default value if not found
            df_bus['vn_kv'] = df_bus['name'].apply(extract_vn)
        
        df_bus['bus_id'] = pd.to_numeric(df_bus['bus_id'], errors='coerce').dropna().astype(int)
        for _, row in df_bus.iterrows():
            bus_id, vn_kv = int(row['bus_id']), float(row['vn_kv'])
            new_idx = pp.create_bus(self.net, name=str(row['name']), vn_kv=vn_kv, in_service=True)
            bus_map[bus_id], bus_vn_map[bus_id] = new_idx, vn_kv
        
        def safe_get_bus_idx(val):
            try: return bus_map.get(int(float(val)))
            except (ValueError, TypeError, KeyError): return None
        
        self._create_elements(self.dataframes, safe_get_bus_idx, bus_vn_map)

        if self.net.ext_grid.empty and self.net.gen.empty:
            slack_bus_idx = self._find_slack_bus(bus_map)
            pp.create_ext_grid(self.net, bus=slack_bus_idx, vm_pu=1.0)
        
        self.logger.info(f"Rede criada: {len(self.net.bus)} barras, {len(self.net.line)} linhas, {len(self.net.trafo)} trafos.")
        return self.net

    def _find_slack_bus(self, bus_map):
        if not self.net.gen.empty: return self.net.gen.bus.iloc[0]
        if bus_map:
            min_original_bus_id = min(bus_map.keys())
            return bus_map[min_original_bus_id]
        if not self.net.bus.empty: return self.net.bus.index[0]
        raise ValueError("Nenhuma barra disponível para criar uma barra de referência (ext_grid).")

    def _create_elements(self, dfs, bus_map_func, bus_vn_map):
        combined_load_gen_dfs = []
        if 'load' in dfs: combined_load_gen_dfs.append(dfs['load'])
        if 'gen' in dfs: combined_load_gen_dfs.append(dfs['gen'])
        if 'load_gen' in dfs: combined_load_gen_dfs.append(dfs['load_gen'])
        
        if combined_load_gen_dfs:
            df_lg = pd.concat(combined_load_gen_dfs, ignore_index=True)
            self._create_loads_gens_from_df(df_lg, bus_map_func)

        if 'shunt' in dfs: self._create_shunts_from_dfs(dfs['shunt'], bus_map_func)
        if 'line' in dfs: self._create_lines_trafos_from_dfs(dfs['line'], bus_map_func, bus_vn_map)

    def _create_loads_gens_from_df(self, df, bus_map_func):
        if df.empty: return
        for _, row in df.iterrows():
            bus_idx = bus_map_func(row.get('bus_id'))
            if bus_idx is None: continue
            
            p_val = row.get('p_mw')
            if pd.notna(p_val):
                p_mw = float(p_val)
                q_mvar = float(row.get('q_mvar', 0.0))
                if p_mw > 0: # It's a load
                    pp.create_load(self.net, bus=bus_idx, p_mw=p_mw, q_mvar=q_mvar)
                elif p_mw < 0: # It's a generator
                    pp.create_gen(self.net, bus=bus_idx, p_mw=-p_mw, vm_pu=1.0)

    def _create_shunts_from_dfs(self, df, bus_map_func):
        if df.empty: return
        for _, row in df.iterrows():
            bus_idx = bus_map_func(row.get('bus_id'))
            if bus_idx is not None and pd.notna(row.get('b_pu')):
                pp.create_shunt(self.net, bus=bus_idx, p_mw=0, q_mvar=float(row['b_pu']) * self.net.sn_mva)
    
    def _create_lines_trafos_from_dfs(self, df, bus_map_func, bus_vn_map):
        if df.empty: return
        for _, row in df.iterrows():
            from_bus_id, to_bus_id = row.get('from_bus'), row.get('to_bus')
            if pd.isna(from_bus_id) or pd.isna(to_bus_id): continue

            from_bus_idx, to_bus_idx = bus_map_func(from_bus_id), bus_map_func(to_bus_id)
            if from_bus_idx is None or to_bus_idx is None: continue
            
            vn_from, vn_to = bus_vn_map.get(int(from_bus_id)), bus_vn_map.get(int(to_bus_id))
            if vn_from is None or vn_to is None: continue
            
            if abs(vn_from - vn_to) > 1: # Transformer
                hv_bus, lv_bus = (from_bus_idx, to_bus_idx) if vn_from > vn_to else (to_bus_idx, from_bus_idx)
                vn_hv, vn_lv = max(vn_from, vn_to), min(vn_from, vn_to)
                pp.create_transformer_from_parameters(self.net, hv_bus=hv_bus, lv_bus=lv_bus, 
                                                      sn_mva=float(row.get('sn_mva', 100.0)), 
                                                      vn_hv_kv=vn_hv, vn_lv_kv=vn_lv, 
                                                      vkr_percent=float(row.get('r_pu', 0.0))*100, 
                                                      vk_percent=float(row.get('x_pu', 0.1))*100, 
                                                      pfe_kw=0, i0_percent=0)
            else: # Line
                z_base = (vn_from**2) / self.net.sn_mva
                r_ohm = float(row.get('r_pu', 0)) * z_base
                x_ohm = float(row.get('x_pu', 0.001)) * z_base
                c_nf = (float(row.get('b_pu', 0)) / (2 * np.pi * 60 * z_base)) * 1e9 if z_base > 0 else 0
                pp.create_line_from_parameters(self.net, from_bus=from_bus_idx, to_bus=to_bus_idx, length_km=1.0, 
                                                r_ohm_per_km=r_ohm, x_ohm_per_km=x_ohm, c_nf_per_km=c_nf, max_i_ka=1.0)

    def run_power_flow(self):
        if self.net is None or self.net.bus.empty:
            raise ValueError("A rede não foi criada ou está vazia.")
        try:
            # Simplified, direct call as requested
            pp.runpp(self.net, algorithm='nr', numba=True)
            
            if self.net.converged:
                self.logger.info("Fluxo de potência convergiu com sucesso")
                return (True, "Fluxo de potência executado com sucesso.")
            else:
                # This case might be less likely to be hit if LoadflowNotConverged is raised
                self.logger.warning("Fluxo de potência não convergiu")
                return (False, "O fluxo de potência NÃO CONVERGIU.")
        except LoadflowNotConverged as e:
            self.logger.error(f"Erro de convergência no fluxo de potência: {e}")
            try: 
                buffer = StringIO()
                sys.stdout = buffer
                pp.diagnostic(self.net)
                sys.stdout = sys.__stdout__ # Restore stdout
                diag_output = buffer.getvalue()
                
                # Create a more user-friendly message
                friendly_message = (
                    f"Falha de convergência: {e}\n\n"
                    "CAUSA PROVÁVEL: Desequilíbrio de dados (ex: sobrecarga severa).\n"
                    "O diagnóstico sugere que o sistema está sobrecarregado. "
                    "Verifique os valores de carga e geração no seu arquivo de entrada.\n\n"
                    f"--- RELATÓRIO DE DIAGNÓSTICO ---\n{diag_output}"
                )
                return False, friendly_message
            except Exception as diag_e: 
                return False, f"Falha no fluxo de potência: {e}\nO diagnóstico também falhou: {diag_e}"
        except Exception as e:
             self.logger.error(f"Erro inesperado no fluxo de potência: {traceback.format_exc()}")
             return False, f"Um erro inesperado ocorreu: {e}"


# =============================================================================
# DIÁLOGO DE CONFIGURAÇÕES
# =============================================================================
class ConfigDialog(QDialog):
    """Dialog para configurações do simulador"""

    def __init__(self, config: SimulationConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Configurações do Simulador")
        self.setModal(True)
        self.resize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout, form_layout = QVBoxLayout(self), QFormLayout()
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(['nr', 'bfsw', 'gs'])
        self.algorithm_combo.setCurrentText(self.config.algorithm)
        form_layout.addRow("Algoritmo:", self.algorithm_combo)

        self.max_iter_spin = QSpinBox()
        self.max_iter_spin.setRange(10, 100); self.max_iter_spin.setValue(self.config.max_iterations)
        form_layout.addRow("Máx. Iterações:", self.max_iter_spin)

        self.tolerance_spin = QDoubleSpinBox()
        self.tolerance_spin.setDecimals(8); self.tolerance_spin.setRange(1e-10, 1e-3); self.tolerance_spin.setValue(self.config.tolerance)
        form_layout.addRow("Tolerância:", self.tolerance_spin)

        self.voltage_min_spin = QDoubleSpinBox()
        self.voltage_min_spin.setRange(0.8, 1.0); self.voltage_min_spin.setSingleStep(0.01); self.voltage_min_spin.setValue(self.config.voltage_limits['min'])
        form_layout.addRow("Tensão Mín (pu):", self.voltage_min_spin)
        
        self.voltage_max_spin = QDoubleSpinBox()
        self.voltage_max_spin.setRange(1.0, 1.2); self.voltage_max_spin.setSingleStep(0.01); self.voltage_max_spin.setValue(self.config.voltage_limits['max'])
        form_layout.addRow("Tensão Máx (pu):", self.voltage_max_spin)
        
        self.enforce_q_check = QCheckBox(); self.enforce_q_check.setChecked(self.config.enforce_q_limits)
        form_layout.addRow("Limites de Q:", self.enforce_q_check)
        
        self.numba_check = QCheckBox(); self.numba_check.setChecked(self.config.numba_acceleration)
        form_layout.addRow("Aceleração Numba:", self.numba_check)
        
        layout.addLayout(form_layout)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_config(self) -> SimulationConfig:
        return SimulationConfig(
            algorithm=self.algorithm_combo.currentText(),
            max_iterations=self.max_iter_spin.value(),
            tolerance=self.tolerance_spin.value(),
            voltage_limits={'min': self.voltage_min_spin.value(), 'max': self.voltage_max_spin.value()},
            enforce_q_limits=self.enforce_q_check.isChecked(),
            numba_acceleration=self.numba_check.isChecked()
        )

# =============================================================================
# WIDGETS DE ALERTAS E LOGS
# =============================================================================
class AlertWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.status_label = QLabel("Status: Aguardando análise...")
        self.status_label.setStyleSheet("QLabel { padding: 10px; border: 2px solid #555; border-radius: 5px; font-weight: bold; font-size: 14px; }")
        layout.addWidget(self.status_label)
        self.alerts_list = QListWidget(); self.alerts_list.setMaximumHeight(150)
        layout.addWidget(self.alerts_list)
        self.recommendations_list = QListWidget(); self.recommendations_list.setMaximumHeight(100)
        layout.addWidget(self.recommendations_list)

    def update_status(self, health_report: Dict[str, Any]):
        status = health_report.get('status', 'UNKNOWN'); message = health_report.get('message', '')
        colors = {'HEALTHY': '#4CAF50', 'WARNING': '#FF9800', 'CRITICAL': '#F44336'}
        color = colors.get(status, '#777')
        self.status_label.setText(f"Status: {status} - {message}")
        self.status_label.setStyleSheet(f"QLabel {{ padding: 10px; border: 2px solid {color}; border-radius: 5px; font-weight: bold; font-size: 14px; background-color: {color}20; color: {color}; }}")
        
        self.alerts_list.clear()
        all_issues = (health_report.get('voltage_issues', []) + health_report.get('loading_issues', []) + health_report.get('stability_issues', []))
        for issue in all_issues: self.alerts_list.addItem(QListWidgetItem(f"⚠ {issue}"))
        
        self.recommendations_list.clear()
        for rec in health_report.get('recommendations', []): self.recommendations_list.addItem(QListWidgetItem(f"💡 {rec}"))
    
    def clear_status(self):
        self.update_status({'status': 'Aguardando', 'message': 'Nenhuma análise executada.'})

class LogWidget(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumHeight(200)
        self.setReadOnly(True)
        self.log_handler = LogHandler(self)
        
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        self.log_handler.setFormatter(formatter)
        
        logging.getLogger().addHandler(self.log_handler)


    def append_log(self, message: str):
        self.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)

class LogHandler(logging.Handler):
    def __init__(self, log_widget):
        super().__init__(); self.log_widget = log_widget
    def emit(self, record):
        self.log_widget.append_log(self.format(record))

# =============================================================================
# THREAD PARA ANÁLISE DE CONTINGÊNCIA
# =============================================================================
class ContingencyThread(QThread):
    progress = Signal(int)
    finished_analysis = Signal(dict)
    error = Signal(str)

    def __init__(self, net, config):
        super().__init__()
        self.net = copy.deepcopy(net)
        self.config = config

    def run(self):
        try:
            analyzer = ContingencyAnalyzer(self.net, self.config)
            results = analyzer.run_n_minus_1_analysis()
            self.finished_analysis.emit(results)
        except Exception as e:
            self.error.emit(str(e))

# =============================================================================
# WIDGETS DE MÉTRICAS E VISUALIZAÇÃO
# =============================================================================
class MetricsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.gen_card = self._create_metric_card("Geração Total (MW)", "N/A")
        self.load_card = self._create_metric_card("Carga Total (MW)", "N/A")
        self.losses_card = self._create_metric_card("Perdas (MW)", "N/A")
        layout.addWidget(self.gen_card)
        layout.addWidget(self.load_card)
        layout.addWidget(self.losses_card)

    def _create_metric_card(self, title, initial_value):
        card, card_layout, value_label = QGroupBox(title), QVBoxLayout(), QLabel(initial_value)
        value_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        value_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(value_label)
        card.setLayout(card_layout)
        return card

    def update_metrics(self, total_gen_mw=0, total_load_mw=0, total_losses_mw=0):
        self.gen_card.findChild(QLabel).setText(f"{total_gen_mw:.2f}" if total_gen_mw is not None else "N/A")
        self.load_card.findChild(QLabel).setText(f"{total_load_mw:.2f}" if total_load_mw is not None else "N/A")
        self.losses_card.findChild(QLabel).setText(f"{total_losses_mw:.2f}" if total_losses_mw is not None else "N/A")

class NetworkCanvas(FigureCanvas):
    def __init__(self, parent=None, logger=None):
        self.fig = plt.figure(figsize=(12, 10), tight_layout=True)
        gs = gridspec.GridSpec(3, 1, height_ratios=[20, 1, 1], hspace=0.1)
        self.ax_diagram = self.fig.add_subplot(gs[0])
        self.ax_legend = self.fig.add_subplot(gs[1])
        self.ax_colorbar = self.fig.add_subplot(gs[2])
        super().__init__(self.fig)
        self.setParent(parent)
        self.logger = logger or logging.getLogger(__name__)
        self.clear_plot()

    def plot_network(self, net, plot_results=False):
        self.clear_plot()
        if not net or net.bus.empty:
            self.ax_diagram.text(0.5, 0.5, 'Nenhuma rede para exibir.', ha='center', va='center', color='gray')
            self.draw(); return
        try:
            if not hasattr(net, 'bus_geodata') or net.bus_geodata.empty:
                pp.plotting.create_generic_coordinates(net, overwrite=True)

            gen_buses = set(net.gen.bus) | set(net.ext_grid.bus) if not (net.gen.empty and net.ext_grid.empty) else set()
            load_buses = set(net.load.bus) if not net.load.empty else set()
            bus_colors = ['#800080' if b in gen_buses and b in load_buses else '#2ca02c' if b in gen_buses else '#ff7f0e' if b in load_buses else '#1f77b4' for b in net.bus.index]
            
            # Fix: Create collections and add them to the axis manually
            bus_collection = plot.create_bus_collection(net, buses=net.bus.index, size=0.08, color=bus_colors, zorder=10)
            self.ax_diagram.add_collection(bus_collection)

            if not net.trafo.empty:
                trafo_collections = plot.create_trafo_collection(net, color='purple', linewidths=1.5, zorder=5)
                # Handle tuple return for newer pandapower versions
                if isinstance(trafo_collections, (list, tuple)):
                    for collection in trafo_collections:
                        self.ax_diagram.add_collection(collection)
                else:
                    self.ax_diagram.add_collection(trafo_collections)
            
            line_handles = []
            if not net.line.empty:
                line_vns = net.bus.loc[net.line.from_bus, 'vn_kv'].values
                vn_kv_unique = sorted(pd.unique(line_vns))
                cmap = plt.get_cmap('viridis', len(vn_kv_unique) + 1)
                for i, v_kv in enumerate(vn_kv_unique):
                    lines_at_v = net.line.index[line_vns == v_kv]
                    if not lines_at_v.empty:
                        line_collection = plot.create_line_collection(net, lines=lines_at_v, color=cmap(i), use_bus_geodata=True, linewidths=1.5, zorder=1)
                        self.ax_diagram.add_collection(line_collection)
                        line_handles.append(Line2D([0], [0], color=cmap(i), lw=2, label=f'{v_kv:.1f} kV'))

            if plot_results and (not net.res_line.empty or not net.res_trafo.empty):
                cmap_res = plt.get_cmap('coolwarm'); 
                all_loadings = []
                if not net.res_line.empty and 'loading_percent' in net.res_line.columns: 
                    all_loadings.extend(net.res_line.loading_percent.dropna().tolist())
                if not net.res_trafo.empty and 'loading_percent' in net.res_trafo.columns: 
                    all_loadings.extend(net.res_trafo.loading_percent.dropna().tolist())
                
                if all_loadings:
                    max_load = max(100, pd.Series(all_loadings).max() * 1.1 if all_loadings else 100)
                    norm = mcolors.Normalize(vmin=0, vmax=max_load)
                    
                    if not net.res_line.empty:
                        lc_res = plot.create_line_collection(net, lines=net.res_line.index, cmap=cmap_res, norm=norm, use_bus_geodata=True, linewidths=2.5, zorder=2)
                        lc_res.set_array(net.res_line.loading_percent.values)
                        self.ax_diagram.add_collection(lc_res)
                    
                    if not net.res_trafo.empty:
                        tc_res_collections = plot.create_trafo_collection(net, cmap=cmap_res, norm=norm, linewidths=2.5, zorder=2)
                        tc_res_array = net.res_trafo.loading_percent.values
                        if isinstance(tc_res_collections, (list, tuple)):
                            for collection in tc_res_collections:
                                collection.set_array(tc_res_array)
                                self.ax_diagram.add_collection(collection)
                        else:
                             tc_res_collections.set_array(tc_res_array)
                             self.ax_diagram.add_collection(tc_res_collections)


                    sm = plt.cm.ScalarMappable(cmap=cmap_res, norm=norm); sm.set_array([])
                    self.fig.colorbar(sm, cax=self.ax_colorbar, label='Carregamento (%)', orientation='horizontal')
            
            bus_handles = [Line2D([0], [0], marker='o', color='w', label='Transfer', markerfacecolor='#1f77b4', markersize=8),
                           Line2D([0], [0], marker='o', color='w', label='Geração', markerfacecolor='#2ca02c', markersize=8),
                           Line2D([0], [0], marker='o', color='w', label='Carga', markerfacecolor='#ff7f0e', markersize=8)]
            self.ax_legend.legend(handles=bus_handles + line_handles, loc='center', ncol=6, frameon=False)

            self.ax_diagram.set_title("Diagrama Unifilar da Rede")
            self.ax_diagram.autoscale_view(); self.ax_diagram.set_xticks([]); self.ax_diagram.set_yticks([])
        except Exception as e:
            self.ax_diagram.text(0.5, 0.5, f'Erro ao desenhar a rede:\n{e}', ha='center', va='center', color='red')
            self.logger.error(f"ERRO ao desenhar diagrama: {traceback.format_exc()}")
        self.draw()

    def clear_plot(self):
        for ax in [self.ax_diagram, self.ax_legend, self.ax_colorbar]: ax.clear()
        self.ax_legend.axis('off'); self.ax_colorbar.axis('off')
        self.draw()

class ResultsPlotsCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig, (self.ax_voltage, self.ax_loading) = plt.subplots(2, 1, figsize=(8, 6), tight_layout=True)
        super().__init__(self.fig)
        self.setParent(parent)
        self.logger = logging.getLogger(__name__)
        self.clear_plots()

    def plot_results(self, net):
        for ax in [self.ax_voltage, self.ax_loading]: ax.clear()
        try:
            if 'res_bus' in net and not net.res_bus.empty:
                bus_voltages = net.res_bus.vm_pu
                combined = pd.concat([bus_voltages.nlargest(10), bus_voltages.nsmallest(10)]).drop_duplicates().sort_values()
                colors = ['#d9534f' if v < 0.95 else '#f0ad4e' if v > 1.05 else '#5cb85c' for v in combined]
                combined.plot(kind='barh', ax=self.ax_voltage, color=colors)
                self.ax_voltage.axvline(x=0.95, color='red', linestyle='--', alpha=0.7, label='Limite Inferior')
                self.ax_voltage.axvline(x=1.05, color='red', linestyle='--', alpha=0.7, label='Limite Superior')
                self.ax_voltage.set_xlabel('Tensão (pu)'); self.ax_voltage.set_ylabel('Barras')
                self.ax_voltage.set_title('Tensões nas Barras (Top 10 Maior/Menor)')
                self.ax_voltage.grid(True, alpha=0.3); self.ax_voltage.legend()

            all_loadings = []
            if 'res_line' in net and not net.res_line.empty and 'loading_percent' in net.res_line:
                all_loadings.append(net.res_line.loading_percent.rename('Linhas'))
            if 'res_trafo' in net and not net.res_trafo.empty and 'loading_percent' in net.res_trafo:
                 all_loadings.append(net.res_trafo.loading_percent.rename('Trafos'))

            if all_loadings:
                loading_series = pd.concat(all_loadings).dropna()
                if not loading_series.empty:
                    top_loaded = loading_series.nlargest(10)
                    colors = ['#d9534f' if v > 100 else '#f0ad4e' if v > 80 else '#5cb85c' for v in top_loaded]
                    top_loaded.plot(kind='barh', ax=self.ax_loading, color=colors)
                    self.ax_loading.axvline(x=100, color='red', linestyle='--', alpha=0.7, label='Limite de Sobrecarga')
                    self.ax_loading.axvline(x=80, color='orange', linestyle='--', alpha=0.7, label='Carregamento Elevado')
                    self.ax_loading.set_xlabel('Carregamento (%)'); self.ax_loading.set_ylabel('Elementos')
                    self.ax_loading.set_title('Top 10 Elementos Mais Carregados')
                    self.ax_loading.grid(True, alpha=0.3); self.ax_loading.legend()
        except Exception as e:
            self.logger.error(f"ERRO ao plotar resultados: {e}")
        self.draw()

    def clear_plots(self):
        for ax in [self.ax_voltage, self.ax_loading]:
            ax.clear()
            ax.text(0.5, 0.5, 'Nenhum resultado para exibir.\nExecute primeiro o fluxo de potência.',
                    ha='center', va='center', transform=ax.transAxes, color='gray')
        self.draw()

# =============================================================================
# JANELA PRINCIPAL APRIMORADA
# =============================================================================
class PowerSystemSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = SimulationConfig.load_from_file("config.json")
        self.model = PowerSystemModel(self.config)
        self.alert_system = AlertSystem(self.config)
        self.logger = setup_logging()
        self.contingency_thread = None
        self.setWindowTitle("Simulador Avançado de Sistemas de Potência v2.0")
        self.setGeometry(100, 100, 1600, 900)
        self.setStyleSheet(AppStyles)
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        self.metrics_widget = MetricsWidget()
        main_layout.addWidget(self.metrics_widget)
        main_splitter = QSplitter(Qt.Horizontal)
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)
        center_panel = self.create_center_panel()
        main_splitter.addWidget(center_panel)
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([350, 800, 450])
        main_layout.addWidget(main_splitter)
        self.clear_all_results()

    def create_left_panel(self):
        panel = QWidget(); layout = QVBoxLayout(panel)
        file_group = QGroupBox("Carregar Dados"); file_layout = QVBoxLayout(file_group)
        load_excel_btn = QPushButton("Carregar Excel"); load_excel_btn.clicked.connect(self.load_excel_data)
        file_layout.addWidget(load_excel_btn)
        load_pwf_btn = QPushButton("Carregar Anarede (.pwf)"); load_pwf_btn.clicked.connect(self.load_pwf_data)
        file_layout.addWidget(load_pwf_btn)
        layout.addWidget(file_group)

        sim_group = QGroupBox("Simulação"); sim_layout = QVBoxLayout(sim_group)
        build_network_btn = QPushButton("Construir Rede"); build_network_btn.setObjectName("build_button"); build_network_btn.clicked.connect(self.build_network)
        sim_layout.addWidget(build_network_btn)
        run_powerflow_btn = QPushButton("Executar Fluxo de Potência"); run_powerflow_btn.setObjectName("run_button"); run_powerflow_btn.clicked.connect(self.run_power_flow)
        sim_layout.addWidget(run_powerflow_btn)
        contingency_btn = QPushButton("Análise de Contingência N-1"); contingency_btn.setObjectName("contingency_button"); contingency_btn.clicked.connect(self.run_contingency_analysis)
        sim_layout.addWidget(contingency_btn)
        self.contingency_progress = QProgressBar(); self.contingency_progress.setVisible(False)
        sim_layout.addWidget(self.contingency_progress)
        config_btn = QPushButton("Configurações"); config_btn.clicked.connect(self.open_config_dialog)
        sim_layout.addWidget(config_btn)
        layout.addWidget(sim_group)

        data_group = QGroupBox("Dados Carregados"); data_layout = QVBoxLayout(data_group)
        self.data_table = QTableWidget(); self.data_table.setMaximumHeight(250)
        data_layout.addWidget(self.data_table)
        export_btn = QPushButton("Exportar Resultados"); export_btn.clicked.connect(self.export_results)
        data_layout.addWidget(export_btn)
        layout.addWidget(data_group)
        layout.addStretch()
        return panel

    def create_center_panel(self):
        panel = QWidget(); layout = QVBoxLayout(panel); tabs = QTabWidget()
        self.network_canvas = NetworkCanvas(logger=self.logger); scroll_area = QScrollArea()
        scroll_area.setWidget(self.network_canvas); scroll_area.setWidgetResizable(True)
        tabs.addTab(scroll_area, "Diagrama Unifilar")
        self.results_canvas = ResultsPlotsCanvas()
        tabs.addTab(self.results_canvas, "Análise de Resultados")
        results_tab = QWidget(); results_layout = QVBoxLayout(results_tab)
        self.results_tabs = QTabWidget()
        self.bus_results_table = QTableWidget()
        self.line_results_table = QTableWidget()
        self.trafo_results_table = QTableWidget()
        self.contingency_results_table = QTableWidget()
        self.results_tabs.addTab(self.bus_results_table, "Resultados Barras")
        self.results_tabs.addTab(self.line_results_table, "Resultados Linhas")
        self.results_tabs.addTab(self.trafo_results_table, "Resultados Trafos")
        self.results_tabs.addTab(self.contingency_results_table, "Contingências")
        results_layout.addWidget(self.results_tabs)
        tabs.addTab(results_tab, "Tabelas de Resultados")
        layout.addWidget(tabs)
        return panel

    def create_right_panel(self):
        panel = QWidget(); layout = QVBoxLayout(panel)
        alerts_group = QGroupBox("Status da Rede e Alertas"); alerts_layout = QVBoxLayout(alerts_group)
        self.alert_widget = AlertWidget(); alerts_layout.addWidget(self.alert_widget)
        layout.addWidget(alerts_group)
        logs_group = QGroupBox("Logs do Sistema"); logs_layout = QVBoxLayout(logs_group)
        self.log_widget = LogWidget(); logs_layout.addWidget(self.log_widget)
        layout.addWidget(logs_group)
        layout.addStretch()
        return panel

    def load_excel_data(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Carregar Ficheiro Excel", "", "Excel Files (*.xlsx *.xls)")
        if filepath:
            try:
                self.logger.info(f"A carregar dados do Excel: {filepath}")
                self.model.load_data_from_excel(filepath)
                self.model._standardize_columns() # Standardize immediately to show user correct names
                self._update_data_table(self.model.dataframes.get('bus', pd.DataFrame()))
                self._show_info_message("Dados do Excel carregados. Próximo passo: Construir a Rede.")
                self.clear_all_results()
            except Exception as e:
                self.logger.error(f"Erro ao carregar Excel: {e}")
                self._show_error_message(f"Falha ao carregar o ficheiro Excel: {e}")
    
    def load_pwf_data(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Carregar Ficheiro Anarede", "", "PWF Files (*.pwf)")
        if filepath:
            try:
                self.logger.info(f"A carregar dados do Anarede: {filepath}")
                self.model.dataframes = AnaredeParser.parse_pwf_to_dataframes(filepath)
                self._update_data_table(self.model.dataframes.get('bus', pd.DataFrame()))
                self._show_info_message("Dados do Anarede carregados. Próximo passo: Construir a Rede.")
                self.clear_all_results()
            except Exception as e:
                self.logger.error(f"Erro ao carregar PWF: {e}")
                self._show_error_message(f"Falha ao carregar o ficheiro PWF: {e}")

    def build_network(self):
        try:
            self.logger.info("A construir a rede pandapower...")
            self.model.create_network_from_dataframes()
            self._show_info_message("Rede construída com sucesso. Próximo passo: Executar Fluxo de Potência.")
            self.network_canvas.plot_network(self.model.net, plot_results=False)
        except Exception as e:
            self.logger.error(f"Erro ao construir a rede: {traceback.format_exc()}")
            self._show_error_message(f"Falha ao construir a rede: {e}")

    def run_power_flow(self):
        try:
            self.logger.info("A executar o fluxo de potência...")
            success, message = self.model.run_power_flow()
            if success:
                self._show_info_message(message)
                self.update_all_visualizations()
            else:
                self._show_error_message(message)
        except Exception as e:
            self.logger.error(f"Erro crítico no fluxo de potência: {e}")
            self._show_error_message(f"Ocorreu um erro inesperado: {e}")

    def run_contingency_analysis(self):
        if self.model.net is None or self.model.net.bus.empty or not self.model.net.converged:
            self._show_error_message("Construa e execute o fluxo de potência base primeiro.")
            return
        self.contingency_progress.setVisible(True)
        self.contingency_progress.setRange(0, 0) # Indeterminate progress
        self.contingency_thread = ContingencyThread(self.model.net, self.config)
        self.contingency_thread.finished_analysis.connect(self._contingency_finished)
        self.contingency_thread.error.connect(self._contingency_error)
        self.contingency_thread.start()
        self.logger.info("Análise de contingência iniciada.")

    def _contingency_finished(self, results):
        self.contingency_progress.setVisible(False)
        if 'error' in results:
            self._show_error_message(f"Erro na análise de contingência: {results['error']}")
            return
        self.logger.info("Análise de contingência concluída.")
        self._show_info_message(f"Análise N-1 concluída. {len(results)} contingências avaliadas.")
        self._update_contingency_table(results)

    def _contingency_error(self, error_msg):
        self.contingency_progress.setVisible(False)
        self.logger.error(f"Erro na thread de contingência: {error_msg}")
        self._show_error_message(f"Erro na análise de contingência: {error_msg}")

    def open_config_dialog(self):
        dialog = ConfigDialog(self.config, self)
        if dialog.exec():
            self.config = dialog.get_config()
            self.model.config = self.config # update model's config
            self.config.save_to_file("config.json")
            self._show_info_message("Configurações atualizadas.")
    
    def export_results(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Exportar Resultados", "", "Excel Files (*.xlsx)")
        if filepath:
            try:
                with pd.ExcelWriter(filepath) as writer:
                    if not self.model.net.res_bus.empty:
                        self.model.net.res_bus.to_excel(writer, sheet_name="Resultados Barras")
                    if not self.model.net.res_line.empty:
                        self.model.net.res_line.to_excel(writer, sheet_name="Resultados Linhas")
                    if not self.model.net.res_trafo.empty:
                        self.model.net.res_trafo.to_excel(writer, sheet_name="Resultados Trafos")
                    if self.contingency_results_table.rowCount() > 0:
                        df_cont = self._get_dataframe_from_table(self.contingency_results_table)
                        df_cont.to_excel(writer, sheet_name="Resultados Contingencia")
                self._show_info_message(f"Resultados exportados para {filepath}")
            except Exception as e:
                self._show_error_message(f"Erro ao exportar resultados: {e}")

    def clear_all_results(self):
        self.metrics_widget.update_metrics(None, None, None)
        self.results_canvas.clear_plots()
        self.network_canvas.clear_plot()
        for table in [self.bus_results_table, self.line_results_table, self.trafo_results_table, self.contingency_results_table]:
            table.setRowCount(0)
            table.setColumnCount(0)
        self.alert_widget.clear_status()

    def update_all_visualizations(self):
        net = self.model.net
        if not net.converged: return
        self._update_metrics()
        self._update_results_tables()
        self._update_health_status()
        self.results_canvas.plot_results(net)
        self.network_canvas.plot_network(net, plot_results=True)

    def _update_data_table(self, df):
        if df is None or df.empty:
            self.data_table.setRowCount(0); self.data_table.setColumnCount(0)
            return
        self.data_table.setRowCount(df.shape[0]); self.data_table.setColumnCount(df.shape[1])
        self.data_table.setHorizontalHeaderLabels(df.columns)
        for i, row in enumerate(df.itertuples(index=False)):
            for j, val in enumerate(row):
                self.data_table.setItem(i, j, QTableWidgetItem(str(val)))
        self.data_table.resizeColumnsToContents()

    def _update_results_tables(self):
        if not self.model.net.converged: return
        self._populate_table(self.bus_results_table, self.model.net.res_bus.round(4))
        self._populate_table(self.line_results_table, self.model.net.res_line.round(4))
        self._populate_table(self.trafo_results_table, self.model.net.res_trafo.round(4))

    def _update_contingency_table(self, results):
        if not results: return
        df = pd.DataFrame.from_dict(results, orient='index')
        df.index.name = 'Contingência'
        df.reset_index(inplace=True)
        self._populate_table(self.contingency_results_table, df)

    def _populate_table(self, table: QTableWidget, df: pd.DataFrame):
        if df.empty: 
            table.setRowCount(0)
            table.setColumnCount(0)
            return
        table.setRowCount(df.shape[0]); table.setColumnCount(df.shape[1])
        table.setHorizontalHeaderLabels([str(c) for c in df.columns])
        for i, row in enumerate(df.itertuples(index=False)):
            for j, val in enumerate(row):
                table.setItem(i, j, QTableWidgetItem(str(val)))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def _update_metrics(self):
        if self.model.net.converged:
            gen_mw = 0
            if not self.model.net.res_gen.empty: gen_mw += self.model.net.res_gen.p_mw.sum()
            if not self.model.net.res_ext_grid.empty: gen_mw += self.model.net.res_ext_grid.p_mw.sum()
            
            load_mw = 0
            if not self.model.net.res_load.empty: load_mw = self.model.net.res_load.p_mw.sum()
            
            losses_mw = gen_mw - load_mw
            self.metrics_widget.update_metrics(gen_mw, load_mw, losses_mw)
    
    def _update_health_status(self):
        if self.model.net.converged:
            report = self.alert_system.analyze_network_health(self.model.net)
            self.alert_widget.update_status(report)

    def _show_error_message(self, message):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setText("Erro")
        msg_box.setInformativeText(message)
        msg_box.setStyleSheet("QMessageBox { background-color: #3C3C3C; color: #F0F0F0; }")
        msg_box.exec()

    def _show_info_message(self, message):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText("Informação")
        msg_box.setInformativeText(message)
        msg_box.setStyleSheet("QMessageBox { background-color: #3C3C3C; color: #F0F0F0; }")
        msg_box.exec()

    def _get_dataframe_from_table(self, table: QTableWidget):
        headers = [table.horizontalHeaderItem(i).text() for i in range(table.columnCount())]
        data = []
        for row in range(table.rowCount()):
            row_data = [table.item(row, col).text() for col in range(table.columnCount())]
            data.append(row_data)
        return pd.DataFrame(data, columns=headers)

    def closeEvent(self, event):
        self.config.save_to_file("config.json")
        super().closeEvent(event)

# =============================================================================
# PONTO DE ENTRADA DA APLICAÇÃO
# =============================================================================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PowerSystemSimulator()
    window.show()
    sys.exit(app.exec())


