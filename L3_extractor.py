import json
import os
import subprocess
import tempfile
from typing import Dict, List, Optional, Set, Tuple

from tracing import trace

### L3 IaC Extractor ###
#
# Turns Terraform (the as-built infrastructure) into L3 RDF individuals that the
# graph can reconcile against the L1/L2 model (the intended architecture). See
# docs/control-modeling.md, "Step 9".
#
# Two things are extracted per significant resource:
#   1. Correspondence -- a `graphix_l2` resource tag declares which L2 element this
#      resource realizes (:L3_realizes). Resources with no tag are emitted anyway,
#      so the conformance analyzer can flag them as unmodeled (shadow) infrastructure.
#   2. Control evidence -- concrete config attributes that show a control is actually
#      realized (e.g. an encrypted RDS instance => :providesControl :EncryptionAtRest).
#      Asserted on the L3 element; the reconciliation step propagates it across
#      :L3_realizes onto the L2 obligation.
#
# We read `terraform show -json` of a plan rather than parsing HCL directly, so that
# Terraform resolves all variables and cross-resource references for us.

NS = "http://thefirm.com/graphix#"

# The resource types that represent architectural *components* (not plumbing such as
# subnets, routes, security groups). Only these become L3 elements -- including when
# untagged, which is exactly how shadow infrastructure surfaces.
SIGNIFICANT_TYPES: Set[str] = {
    "aws_apigatewayv2_api",
    "aws_lb",
    "aws_ecs_service",
    "aws_db_instance",
}

# The provider config skip-flags needed so `terraform plan` does not call AWS STS to
# validate credentials (this is test data, never applied). Dropped into the working
# dir as an override file and removed afterwards -- the fixture is left untouched.
_OVERRIDE_TF = """
provider "aws" {
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true
}
"""


def _terraform_json(tf_dir: str) -> dict:
    """Run `terraform plan` + `show -json` in tf_dir and return the parsed JSON."""
    override = os.path.join(tf_dir, "zz_graphix_override.tf")
    plan_file = os.path.join(tempfile.gettempdir(), "graphix_tf.plan")
    env = {**os.environ, "AWS_DEFAULT_REGION": os.environ.get("AWS_DEFAULT_REGION", "us-east-1")}
    try:
        with open(override, "w") as f:
            f.write(_OVERRIDE_TF)
        trace("🌍 Running terraform plan (offline, dummy creds)...")
        subprocess.run(
            ["terraform", "plan", "-out", plan_file, "-input=false", "-no-color"],
            cwd=tf_dir, env=env, check=True, capture_output=True, text=True)
        show = subprocess.run(
            ["terraform", "show", "-json", plan_file],
            cwd=tf_dir, env=env, check=True, capture_output=True, text=True)
        return json.loads(show.stdout)
    except subprocess.CalledProcessError as e:
        trace(f"🧨 terraform failed: {e.stderr or e.stdout}")
        raise
    finally:
        if os.path.exists(override):
            os.remove(override)
        if os.path.exists(plan_file):
            os.remove(plan_file)


def _resources(tf_json: dict) -> List[dict]:
    return tf_json.get("planned_values", {}).get("root_module", {}).get("resources", [])


def _uri(address: str) -> str:
    # aws_db_instance.postgres -> L3_aws_db_instance_postgres
    return "L3_" + address.replace(".", "_").replace("[", "_").replace("]", "")


def _control_evidence(res: dict, has_authorizer: bool, lb_has_tls: bool) -> List[str]:
    """Controls this resource demonstrably *provides*, read from concrete config."""
    rtype = res["type"]
    vals = res.get("values", {})
    controls: List[str] = []

    if rtype == "aws_db_instance":
        # Encryption at rest is realized when the volume is encrypted.
        if vals.get("storage_encrypted") is True:
            controls.append("EncryptionAtRest")

    elif rtype == "aws_apigatewayv2_api":
        # The managed execute-api endpoint is always served over TLS.
        controls.append("TrafficEncryption")
        # Client authentication is realized only when an authorizer is attached.
        if has_authorizer:
            controls.append("ClientAuthentication")

    elif rtype == "aws_lb":
        # A load balancer terminates TLS only if it has an HTTPS listener.
        if lb_has_tls:
            controls.append("TrafficEncryption")

    return controls


def ExtractIaC(tf_dir: str, out_path: str) -> str:
    """Extract L3 individuals from the Terraform in tf_dir, write Turtle to out_path."""
    tf_json = _terraform_json(tf_dir)
    resources = _resources(tf_json)

    # Global signals that a per-resource rule needs (single-API / single-LB test data;
    # a fuller version would resolve these by reference in the `configuration` block).
    has_authorizer = any(r["type"] == "aws_apigatewayv2_authorizer" for r in resources)
    lb_has_tls = any(
        r["type"] == "aws_lb_listener" and r.get("values", {}).get("protocol") == "HTTPS"
        for r in resources)

    lines: List[str] = [
        "@prefix : <http://thefirm.com/graphix#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "",
        "#################################################################",
        "#    L3 (as-built) -- extracted from Terraform by L3_extractor.py",
        "#################################################################",
        "",
    ]

    count = 0
    for res in resources:
        if res["type"] not in SIGNIFICANT_TYPES:
            continue
        count += 1
        uri = _uri(res["address"])
        vals = res.get("values", {})
        tags = vals.get("tags") or {}
        label = tags.get("Name") or res["address"]
        realizes: Optional[str] = tags.get("graphix_l2")
        controls = _control_evidence(res, has_authorizer, lb_has_tls)

        lines.append(f"# {res['address']}")
        lines.append(f":{uri} a :L3_Element ;")
        lines.append(f'    rdfs:label "{label}" ;')
        lines.append(f'    :L3_awsResourceType "{res["type"]}" .')
        if realizes:
            lines.append(f":{uri} :L3_realizes :{realizes} .")
        else:
            lines.append(f"# (no graphix_l2 tag -> unmodeled / shadow candidate)")
        for c in controls:
            lines.append(f":{uri} :providesControl :{c} .")
        lines.append("")

    with open(out_path, "w") as f:
        f.write("\n".join(lines))

    trace(f"🧱 Extracted {count} L3 element(s) to {out_path}")
    return out_path
