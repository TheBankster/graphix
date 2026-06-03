import sys
import argparse
import threading
#from graphixconfig import LoadGraphixConfig, GraphDBRepoId
#from tracing import trace
#from graphdb import StartGraphClients, GraphDBLabel, UploadTtl, ClearRepository

def main(args):
    # LoadGraphixConfig('graphix.config')

    parser = argparse.ArgumentParser(description='GRAPHIX Prototype')
    parser.add_argument(
        "-s", "--schema",
        help="Path to the .ttl file containing the schema",
        metavar="FILE")
    parser.add_argument(
        "-d", "--data",
        help="Path to the .ttl file containing initial data",
        metavar="FILE")
    parser.add_argument(
        "-c", "--clear-repo",
        action="store_const",
        const="ClearRepo",
        dest="func",
        help="Clear the GRAPHIX repository")
    parsed_args = parser.parse_args(args)

    # Connect to event and graph databases
    # StartGraphClients()

    # Everything below assumes that the GRAPHIX repository already exists
"""
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
    return
"""
if __name__ == "__main__":
    main(sys.argv[1:])