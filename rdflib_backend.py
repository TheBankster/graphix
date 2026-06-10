import os
import rdflib
import owlrl
from typing import Any
from tracing import trace

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_FILE = os.path.join(_SCRIPT_DIR, "graphix_data.ttl")

_graph: rdflib.Graph = None

def _infer(g: rdflib.Graph) -> None:
    # OWL2-RL (not just RDFS): needed so owl:hasValue archetype restrictions, owl:unionOf
    # domains, subproperty entailment, etc. materialise -- the local mirror of GraphDB's
    # owl2-rl-optimized ruleset. Under RDFS_Semantics the control-provider "capable" tier
    # is inert (POTENTIAL collapses to OPEN; see docs/control-modeling.md Step 3).
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)

def _load() -> rdflib.Graph:
    g = rdflib.Graph()
    if os.path.exists(_DATA_FILE):
        g.parse(_DATA_FILE, format="turtle")
        _infer(g)
    return g

def _save(g: rdflib.Graph) -> None:
    g.serialize(destination=_DATA_FILE, format="turtle")

def StartGraphClients(host: str, port: int, repoid: str) -> None:
    global _graph
    _graph = _load()
    trace("📡 StartGraphClients (rdflib): graph loaded from disk")

def GetBindings(query: str) -> Any:
    results = _graph.query(query)
    bindings = []
    for row in results:
        binding = {}
        for var in results.vars:
            val = row[var]
            if val is None:
                continue
            if isinstance(val, rdflib.URIRef):
                binding[str(var)] = {"type": "uri", "value": str(val)}
            elif isinstance(val, rdflib.Literal):
                binding[str(var)] = {"type": "literal", "value": str(val)}
            else:
                binding[str(var)] = {"type": "bnode", "value": str(val)}
        bindings.append(binding)
    return bindings

def UploadTtl(repo_id: str, file_path: str, label: Any) -> None:
    if not os.path.exists(file_path):
        trace(f"🧨 Error: {label.value} file '{file_path}' not found.")
        exit(1)
    trace(f"📤 Uploading {label.value} from {file_path}...")
    _graph.parse(file_path, format="turtle")
    _infer(_graph)
    _save(_graph)
    trace(f"✅ Successfully uploaded {label.value}.")

def RunUpdate(update: str) -> None:
    # SPARQL UPDATE (INSERT/DELETE) against the in-memory graph, then re-infer and persist.
    # Mirrors graphdb.RunUpdate so the L2 control modeler + L3 reconciler work unchanged.
    _graph.update(update)
    _infer(_graph)
    _save(_graph)

def ClearRepository(repo_id: str) -> None:
    global _graph
    _graph = rdflib.Graph()
    if os.path.exists(_DATA_FILE):
        os.remove(_DATA_FILE)
    trace(f"🧹 Successfully cleared repository '{repo_id}' (rdflib).")
