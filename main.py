import sys
import argparse
from graphixconfig import LoadGraphixConfig, GraphDBRepoId
from tracing import trace
from graphdb import StartGraphClients, GraphDBLabel, UploadTtl, ClearRepository
from L1_analyzer import L1_SemanticAnalyzer
from L2_analyzer import L2_SemanticAnalyzer
from L1_modeler import L1_ThreatModeler

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
        "-a", "--semantic-analyzer",
        action="store_const",
        const="Analyze",
        dest="func",
        help="Rung the semantic analyzer on the entire repository")
    parser.add_argument(
        "-t", "--threat-modeler",
        action="store_const",
        const="ThreatModel",
        dest="func",
        help="Run the threat modeler on the entire repository")
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
    elif parsed_args.func == "ClearRepo":
        ClearRepository(repo_id=GraphDBRepoId)
    elif parsed_args.func == "Analyze":
        checkPassed: bool
        checkPassed = L1_SemanticAnalyzer()
        if (checkPassed):
            checkPassed = L2_SemanticAnalyzer()
    elif parsed_args.func == "ThreatModel":
        L1_ThreatModeler()
    else:
        parser.print_help()
    return

if __name__ == "__main__":
    main(sys.argv[1:])