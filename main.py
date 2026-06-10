import sys
import argparse
from graphixconfig import LoadGraphixConfig, GraphDBRepoId
from tracing import trace
from graphdb import StartGraphClients, GraphDBLabel, UploadTtl, ClearRepository
from L1_analyzer import L1_SemanticAnalyzer
from L2_analyzer import L2_SemanticAnalyzer
from L1_modeler import L1_ThreatModeler
from L2_modeler import L2_ThreatModeler
from L2_control_modeler import L2_ControlModeler
from L3_extractor import ExtractIaC
from L3_analyzer import L3_Reconciler

def main(args):
    LoadGraphixConfig('graphix.config')

    parser = argparse.ArgumentParser(description='GRAPHIX Prototype')
    parser.add_argument(
        "-s", "--schema",
        help="Path to the .ttl file containing the schema",
        metavar="FILE")
    parser.add_argument(
        "-d", "--data",
        help="Path to the .ttl file containing data",
        metavar="FILE")
    parser.add_argument(
        "-c", "--clear-repo",
        action="store_const",
        const="ClearRepo",
        dest="func",
        help="Clear the GRAPHIX repository")
    parser.add_argument(
        "-1", "--semantic-analyzer-1",
        action="store_const",
        const="AnalyzeL1",
        dest="func",
        help="Rung the L1 semantic analyzer on the entire repository")
    parser.add_argument(
        "-2", "--semantic-analyzer-2",
        action="store_const",
        const="AnalyzeL2",
        dest="func",
        help="Rung the L2 semantic analyzer on the entire repository")
    parser.add_argument(
        "-t", "--threat-modeler",
        action="store_const",
        const="ThreatModel",
        dest="func",
        help="Run the threat modeler on the entire repository")
    parser.add_argument(
        "-m", "--control-modeler",
        action="store_const",
        const="ControlModel",
        dest="func",
        help="Derive control obligations from zone-crossing policy and report satisfaction")
    parser.add_argument(
        "-x", "--extract-iac",
        help="Extract L3 (as-built) elements from the Terraform in DIR and load them",
        metavar="DIR")
    parser.add_argument(
        "-r", "--reconcile",
        action="store_const",
        const="Reconcile",
        dest="func",
        help="Reconcile L3 (as-built) against the L1/L2 model: propagate control "
             "evidence and report conformance")
    parsed_args = parser.parse_args(args)

    # Connect to graph database
    StartGraphClients()

    # Everything below assumes that the GRAPHIX repository already exists
    if parsed_args.schema:
        trace(f"📥 Schema file provided: {parsed_args.schema}")
        UploadTtl(
            repo_id=GraphDBRepoId,
            file_path=parsed_args.schema,
            label=GraphDBLabel.SCHEMA)
    elif parsed_args.data:
        trace(f"📥 Data file provided: {parsed_args.data}")
        UploadTtl(
            repo_id=GraphDBRepoId,
            file_path=parsed_args.data,
            label=GraphDBLabel.DATA)
    elif parsed_args.extract_iac:
        trace(f"🏗️  Extracting L3 from IaC: {parsed_args.extract_iac}")
        # Write the fixture into tests/ alongside the L1/L2 fixtures, regardless of
        # whether we were invoked from the repo root or from tests/ (as runall.sh does).
        import os
        out_dir = os.path.join(os.path.dirname(os.path.normpath(parsed_args.extract_iac)), "tests")
        out_path = ExtractIaC(parsed_args.extract_iac, os.path.join(out_dir, "L3_extracted.ttl"))
        UploadTtl(
            repo_id=GraphDBRepoId,
            file_path=out_path,
            label=GraphDBLabel.DATA)
    elif parsed_args.func == "ClearRepo":
        ClearRepository(repo_id=GraphDBRepoId)
    elif parsed_args.func == "AnalyzeL1":
        L1_SemanticAnalyzer()
    elif parsed_args.func == "AnalyzeL2":
        L2_SemanticAnalyzer()
    elif parsed_args.func == "ThreatModel":
        L1_ThreatModeler()
        L2_ThreatModeler()
    elif parsed_args.func == "ControlModel":
        L2_ControlModeler()
    elif parsed_args.func == "Reconcile":
        L3_Reconciler()
    else:
        parser.print_help()
    return

if __name__ == "__main__":
    main(sys.argv[1:])