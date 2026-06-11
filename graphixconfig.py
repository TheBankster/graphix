import tracing
import tomllib
import os

# --- Defaults ---
DefaultGraphDBHost = "localhost"
DefaultGraphDBPort = 7200
DefaultGraphDBRepoId = "GRAPHIX"
DefaultGraphDBBackend = "graphdb"

# --- Global State ---
GraphDBHost: str = DefaultGraphDBHost
GraphDBPort: int = DefaultGraphDBPort
GraphDBRepoId: str = DefaultGraphDBRepoId
GraphDBBackend: str = DefaultGraphDBBackend

def LoadGraphixConfig(configFile: str) -> None:
    global GraphDBHost, GraphDBPort, GraphDBRepoId, GraphDBBackend
    
    # Determine the directory containing this script
    program_dir = os.path.dirname(os.path.abspath(__file__))

    try:
        # Build the absolute path to the config file
        config_path = os.path.join(program_dir, configFile)
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Graphix config file not found: {configFile}")

        with open(config_path, "rb") as f:
            config = tomllib.load(f)

        # tomllib supports nested dictionaries naturally
        graph_cfg = config.get('graphdb', {})
        GraphDBHost = graph_cfg.get('host', DefaultGraphDBHost)
        GraphDBPort = graph_cfg.get('port', DefaultGraphDBPort)
        GraphDBRepoId = graph_cfg.get('repoid', DefaultGraphDBRepoId)
        GraphDBBackend = graph_cfg.get('backend', DefaultGraphDBBackend)

        # Settings section
        settings_cfg = config.get('settings', {})
        tracing.Tracing = settings_cfg.get('tracing', False)
        
        print(f"🛠️ Tracing is: {tracing.Tracing}")

    except FileNotFoundError:
        print(f"🧨 Control config file not found: {configFile}")
    except Exception as e:
        print(f"🧨 Failed to load TOML config file {configFile}: {e}")