#!/usr/bin/env python3
"""
Arquivo de configuração para o Dashboard RCE Framework.
Centraliza todas as configurações e opções do sistema.
"""

import os
from pathlib import Path

variables_decision_IEEE_118 = [24,3,24,26,1,24,24,27,24,24]
variables_decision_IEEE_14 = [
        14,
        15,
        14,
        18,
        20
    ]

class DashboardConfig:
    """Configurações centralizadas do dashboard."""
    
    # === CONFIGURAÇÕES DE DIRETÓRIOS ===
    BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
    SRC_DIR = BASE_DIR / "src"
    OUTPUT_DIR = SRC_DIR / "output"
    COMPONENTS_DIR = SRC_DIR / "DashboardApp" / "views" / "Screens" / "components"
    
    # === CONFIGURAÇÕES DE ARQUIVOS ===
    PARAMS_FILE = SRC_DIR / "params.json"
    OPTIONS_FILE = SRC_DIR / "options.json"
    CONSOLIDATED_RESULTS_FILE = OUTPUT_DIR / "resultados_consolidados.xlsx"
    POP_FINAL_FILE = OUTPUT_DIR / "pop_final.xlsx"
    
    # === CONFIGURAÇÕES DE INTERFACE ===
    PAGE_ICON = "⚡"
    PAGE_TITLE = f"{PAGE_ICON} Dashboard RCE Framework"

    LAYOUT = "wide"
    INITIAL_SIDEBAR_STATE = "expanded"
    
    # === CONFIGURAÇÕES DE TABS ===
    TAB_NAMES = {
        "solution": "🏆 Solução",
        "convergence": "📈 Gráfico de Convergência", 
        "statistics": "📊 Estatísticas",
        "scheduling": "🎯 Agendamento",
        
    }
    
    # === CONFIGURAÇÕES DE VISUALIZAÇÃO ===
    CHART_HEIGHT = 400
    CHART_WIDTH = 800
    MAX_ROWS_IN_TABLE = 100
    DEBUG_MODE = False
    
    # === CONFIGURAÇÕES DE CACHE ===
    CACHE_TTL = 3600  # 1 hora em segundos
    MAX_CACHE_SIZE = 1000
    
    # === CONFIGURAÇÕES DE EXPORTAÇÃO ===
    EXPORT_FORMATS = ["xlsx"]
    DEFAULT_EXPORT_FORMAT = "xlsx"
    
    # === CONFIGURAÇÕES DE LOGGING ===
    LOG_LEVEL = "INFO"
    LOG_FILE = BASE_DIR / "dashboard.log"
    ENABLE_CONSOLE_LOGGING = True
    
    # === CONFIGURAÇÕES DE PERFORMANCE ===
    ENABLE_LAZY_LOADING = True
    BATCH_SIZE = 50
    MAX_CONCURRENT_REQUESTS = 5
    
    # === CONFIGURAÇÕES DE SEGURANÇA ===
    ENABLE_DEBUG_INFO = False
    SHOW_SYSTEM_PATHS = False
    ENABLE_FILE_DOWNLOAD = True
    
    # === CONFIGURAÇÕES DE COMPONENTES ===
    COMPONENTS = {
        "CardSolutions": {
            "enabled": True,
            "fallback_enabled": True,
            "max_variables_display": 12
        },
        "StatisticsTableComponent": {
            "enabled": True,
            "fallback_enabled": True,
            "max_rows": 100
        },
        "AgendamentoRedePage": {
            "enabled": True,
            "fallback_enabled": True,
            "timeline_height": 300
        }
    }
    
    # === CONFIGURAÇÕES DE VALIDAÇÃO ===
    VALIDATION = {
        "required_columns": {
            "config": ['config_num', 'config',  'configuracao', ],
            "exec": ['exec_num', 'exec', 'run', 'execucao', ]
        },
        "data_types": {
            "config_num": ["int", "str"],
            "exec_num": ["int", "str"],
            "best_fitness": ["float", "int"],
            "best_gen_idx": ["int", "str"]
        }
    }
    
    # === CONFIGURAÇÕES DE MENSAGENS ===
    MESSAGES = {
        "success": {
            "system_loaded": "✅ Sistema carregado com sucesso!",
            "consolidation_complete": "✅ Consolidação concluída!",
            "export_complete": "✅ Exportação concluída!",
            "cache_cleared": "✅ Cache limpo com sucesso!"
        },
        "warning": {
            "system_not_loaded": "⚠️ Sistema não carregado",
            "no_data": "⚠️ Nenhum dado disponível",
            "component_unavailable": "⚠️ Componente não disponível"
        },
        "error": {
            "critical_error": "❌ Erro crítico no dashboard",
            "consolidation_error": "❌ Erro na consolidação",
            "export_error": "❌ Erro na exportação",
            "cache_error": "❌ Erro ao limpar cache"
        },
        "info": {
            "try_reload": "🔧 Tente recarregar a página ou verificar os dados.",
            "check_components": "🔧 Verifique se todos os componentes estão disponíveis.",
            "contact_support": "📞 Entre em contato com o suporte se o problema persistir."
        }
    }
    
    @classmethod
    def get_output_dir(cls) -> Path:
        """Retorna o diretório de saída, criando se não existir."""
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        return cls.OUTPUT_DIR
    
    @classmethod
    def get_component_path(cls, component_name: str) -> Path:
        """Retorna o caminho para um componente específico."""
        return cls.COMPONENTS_DIR / f"{component_name}.py"
    
    @classmethod
    def is_component_enabled(cls, component_name: str) -> bool:
        """Verifica se um componente está habilitado."""
        return cls.COMPONENTS.get(component_name, {}).get("enabled", True)
    
    @classmethod
    def get_component_config(cls, component_name: str) -> dict:
        """Retorna a configuração de um componente específico."""
        return cls.COMPONENTS.get(component_name, {})
    
    @classmethod
    def get_message(cls, category: str, key: str) -> str:
        """Retorna uma mensagem específica da configuração."""
        return cls.MESSAGES.get(category, {}).get(key, f"Message not found: {category}.{key}")
    
    @classmethod
    def validate_environment(cls) -> bool:
        """Valida se o ambiente está configurado corretamente."""
        required_dirs = [cls.SRC_DIR, cls.OUTPUT_DIR, cls.COMPONENTS_DIR]
        required_files = [cls.PARAMS_FILE, cls.OPTIONS_FILE]
        
        for directory in required_dirs:
            if not directory.exists():
                print(f"❌ Diretório não encontrado: {directory}")
                return False
        
        for file_path in required_files:
            if not file_path.exists():
                print(f"⚠️ Arquivo não encontrado: {file_path}")
        
        print("✅ Ambiente validado com sucesso!")
        return True

# Configurações específicas para desenvolvimento
class DevConfig(DashboardConfig):
    """Configurações específicas para desenvolvimento."""
    DEBUG_MODE = True
    ENABLE_DEBUG_INFO = True
    SHOW_SYSTEM_PATHS = True
    LOG_LEVEL = "DEBUG"

# Configurações específicas para produção
class ProdConfig(DashboardConfig):
    """Configurações específicas para produção."""
    DEBUG_MODE = False
    ENABLE_DEBUG_INFO = False
    SHOW_SYSTEM_PATHS = False
    LOG_LEVEL = "WARNING"
    ENABLE_LAZY_LOADING = True

# Configuração padrão baseada no ambiente
def get_config():
    """Retorna a configuração apropriada baseada no ambiente."""
    env = os.getenv("DASHBOARD_ENV", "development").lower()
    
    if env == "production":
        return ProdConfig()
    else:
        return DevConfig()

# Para uso direto
if __name__ == "__main__":
    config = get_config()
    print(f"🔧 Configuração carregada: {config.__class__.__name__}")
    print(f"📁 Base Directory: {config.BASE_DIR}")
    print(f"🐛 Debug Mode: {config.DEBUG_MODE}")
    
    # Valida ambiente
    config.validate_environment() 