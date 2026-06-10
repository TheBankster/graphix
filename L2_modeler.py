from graphdb import GetBindings
from stride import STRIDE
from controls import CONTROL
from typing import Set, Tuple, FrozenSet

### L2 Threat Modeling Rules ###

# Each Threat Model analysis returns a set of tuples, each containing:
#   - STRIDE threat (from the list above)
#   - Tuple of graph node URIs and controls employed for mitigations:
#       - Attacker URI 
#       - Vulnerable Party URI
#       - URI of the entity employing the control
#       - Control type
