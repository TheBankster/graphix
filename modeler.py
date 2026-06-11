from typing import Iterable, Tuple, FrozenSet, Dict
from collections import defaultdict
from stride import STRIDE
from controls import CONTROL

# Mapping of controls to the primary STRIDE threat they mitigate
CONTROL_TO_STRIDE: Dict[CONTROL, STRIDE] = {
    CONTROL.CLIENT_AUTHENTICATION: STRIDE.SPOOFING,
    CONTROL.SERVER_AUTHENTICATION: STRIDE.SPOOFING,
    CONTROL.ACCESS_CONTROL: STRIDE.ELEVATION_OF_PRIVILEGE,
    CONTROL.RATE_LIMITING: STRIDE.DENIAL_OF_SERVICE,
    CONTROL.DATA_IN_TRANSIT_ENCRYPTION: STRIDE.INFORMATION_DISCLOSURE,
    CONTROL.DATA_AT_REST_ENCRYPTION: STRIDE.INFORMATION_DISCLOSURE,
}

# Mapping of URI fragments from the schema to CONTROL enum
URI_TO_CONTROL: Dict[str, CONTROL] = {
    "CTL_ClientAuthentication": CONTROL.CLIENT_AUTHENTICATION,
    "CTL_ServerAuthentication": CONTROL.SERVER_AUTHENTICATION,
    "CTL_AccessControl": CONTROL.ACCESS_CONTROL,
    "CTL_RateLimiting": CONTROL.RATE_LIMITING,
    "CTL_DataInTransitEncryption": CONTROL.DATA_IN_TRANSIT_ENCRYPTION,
    "CTL_DataAtRestEncryption": CONTROL.DATA_AT_REST_ENCRYPTION,
}

def RenderThreats(results: Iterable[Tuple[STRIDE, FrozenSet[Tuple[str, str, str, CONTROL, bool]]]]) -> None:
    # 1. Bucket the inner entries by their STRIDE threat type
    grouped_threats = defaultdict(list)
    for stride_type, entries_set in results:
        for entry in entries_set:
            grouped_threats[stride_type].append(entry)
            
    # 2. Iterate through the grouped categories in alphabetical order of the threat name
    for stride_type in sorted(grouped_threats.keys(), key=lambda x: x.value):
        entries = grouped_threats[stride_type]
        
        # Determine if the ENTIRE category is mitigated (True if ALL entries are true)
        all_mitigated = all(entry[4] for entry in entries)
        category_icon = "✅" if all_mitigated else "⚠️ "
        
        # Print the overarching threat category header ONCE
        print(f"\n{category_icon} Threat Category: {stride_type.value}")
        
        # Print each individual target link under this header
        for entry in entries:
            # Check the status of this specific link
            item_icon = "✅" if entry[4] else "⚠️ "
            
            print(f"    ---------------------------------------------")
            print(f"    Attacker node:      {entry[0]}")
            print(f"    Vulnerable node:    {entry[1]}")
            print(f"    Mitigating entity:  {entry[2]}")
            print(f"    Mitigating control: {entry[3].value} {item_icon}")