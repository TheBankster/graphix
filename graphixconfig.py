import tracing
import tomllib
import os

# --- Defaults ---
DefaultGraphDBHost = "localhost"
DefaultGraphDBPort = 7200
DefaultGraphDBRepoId = "GRAPHIX"

# --- Global State ---
GraphDBHost: str = DefaultGraphDBHost
GraphDBPort: int = DefaultGraphDBPort
GraphDBRepoId: str = DefaultGraphDBRepoId

def LoadGraphixConfig(configFile: str) -> None:
    global GraphDBHost, GraphDBPort, GraphDBRepoId
    
    if not os.path.exists(configFile):
        print(f"⚠️ Configuration file {configFile} not found. Using defaults.")
        return

    try:
        with open(configFile, "rb") as f:
            config = tomllib.load(f)

        # tomllib supports nested dictionaries naturally
        graph_cfg = config.get('graphdb', {})
        GraphDBHost = graph_cfg.get('host', DefaultGraphDBHost)
        GraphDBPort = graph_cfg.get('port', DefaultGraphDBPort)
        GraphDBRepoId = graph_cfg.get('repoid', DefaultGraphDBRepoId)

        # Settings section
        settings_cfg = config.get('settings', {})
        tracing.Tracing = settings_cfg.get('tracing', False)
        
        print(f"🛠️ Tracing is: {tracing.Tracing}")

    except FileNotFoundError:
        print(f"🧨 Control config file not found: {configFile}")
    except Exception as e:
        print(f"🧨 Failed to load TOML config file {configFile}: {e}")