import os
import requests
from graphixconfig import GraphDBHost, GraphDBPort, GraphDBRepoId
from tracing import trace
from enum import Enum
from SPARQLWrapper import JSON, POST, SPARQLWrapper
from typing import Any, cast, Dict, Optional

_GraphQueryClient: Optional[SPARQLWrapper] = None
_GraphUpdateClient: Optional[SPARQLWrapper] = None

class GraphDBLabel(Enum):
    SCHEMA = "Schema"
    DATA = "Data"

def GraphDBUriPrefix(host:str = GraphDBHost, port:int = GraphDBPort) -> str:
    return f"http://{host}:{port}"

def GraphDBUri(host:str = GraphDBHost, port:int = GraphDBPort, repoid:str = GraphDBRepoId):
    return GraphDBUriPrefix(host, port) + f"/repositories/{repoid}"

# Checks if a repository exists using the GraphDB REST Management API.
def CheckRepositoryExists(host: str, port: int, repoid: str) -> bool:
    url = GraphDBUriPrefix(host, port) + f"/rest/repositories"
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # The API returns a list of repository objects
        repos = response.json()
        
        # Check if any repository has the matching ID
        return any(repo['id'] == repoid for repo in repos)
    except Exception as e:
        trace(f"❌ Error checking repository existence: {e}")
        return False
# Generic function to upload TTL files to GraphDB.
def UploadTtl(repo_id:str, file_path:str, label:GraphDBLabel):
    if not os.path.exists(file_path):
        trace(f"🧨 Error: {label.value} file '{file_path}' not found.")
        exit(1)
        return

    url = GraphDBUriPrefix() + f"/repositories/{repo_id}/statements"
    headers = {"Content-Type": "text/turtle"}

    trace(f"📤 Uploading {label.value} from {file_path}...")
    try:
        with open(file_path, 'rb') as f:
            response = requests.post(url, data=f, headers=headers)
        
        if response.status_code in [200, 204]:
            trace(f"✅ Successfully uploaded {label.value}.")
        else:
            trace(f"🧨 Failed to upload {label.value}. Status: {response.status_code}. Response: {response.text}")
            exit(1)
    except Exception as e:
        trace(f"🧨 An error occurred during {label.value} upload: {e}")
        exit(1)

# Clears all data from the specified GraphDB repository.
def ClearRepository(repo_id:str):
    url = GraphDBUriPrefix() + f"/repositories/{repo_id}/statements"
    try:
        # Sending DELETE request with an empty 'update' or no params 
        # clears all triples in all contexts (graphs)
        response = requests.delete(url)
        if response.status_code in [200, 204]:
            trace(f"🧹 Successfully cleared repository '{repo_id}'.")
        else:
            trace(f"🧨 Failed to clear repository '{repo_id}'. Status: {response.status_code}. Response: {response.text}")
            exit(1)
    except Exception as e:
        trace(f"🧨 An error occurred while clearing repository '{repo_id}': {e}")
        exit(1)

def StartGraphClients(host:str=GraphDBHost, port:int=GraphDBPort, repoid:str=GraphDBRepoId) -> None:
    global _GraphQueryClient, _GraphUpdateClient
    try:
        if not CheckRepositoryExists(host, port, repoid):
            raise ValueError(f"GraphDB repository '{repoid}' does not exist at {host}:{port}")
        _GraphQueryClient = SPARQLWrapper(GraphDBUri(host, port, repoid))
        _GraphUpdateClient = SPARQLWrapper(GraphDBUri(host, port, repoid) + "/statements")
        trace("📡 StartGraphClients: GraphClients connected successfully")
    except Exception as e:
        trace(f"🧨 StartGraphClients: Failed to initialize or connect Graph Clients: {e}")
        raise

def GraphQueryClient() -> SPARQLWrapper:
    global _GraphQueryClient
    if _GraphQueryClient is None:
        raise RuntimeError("🧨 Clients not initialized! Call StartGraphClients() first.")
    return _GraphQueryClient

def GraphUpdateClient() -> SPARQLWrapper:
    global _GraphUpdateClient
    if _GraphUpdateClient is None:
        raise RuntimeError("🧨 Clients not initialized! Call StartGraphClients() first.")
    return _GraphUpdateClient

def GetBindings(query: str) -> Any:
    client = GraphQueryClient()
    client.setQuery(query)
    client.setReturnFormat(JSON)
    raw_results = client.query().convert()
    results = cast(Dict[str, Any], raw_results)
    bindings = results["results"]["bindings"]
    return bindings

# Runs a SPARQL UPDATE (e.g. INSERT/DELETE) against the repository.
def RunUpdate(update: str) -> None:
    client = GraphUpdateClient()
    client.setQuery(update)
    client.setMethod(POST)
    client.query()
