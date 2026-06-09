from enum import Enum

# NOTE: These controls are also defined canonically in the ontology (schema.ttl,
# "Control Catalog" section) as individuals of :Control. Each enum value below
# matches the rdfs:label of the corresponding individual; keep the two in sync.
# See docs/control-modeling.md.
class CONTROL(Enum):
    CLIENT_AUTHENTICATION = "Client Authentication"
    SERVER_AUTHENTICATION = "Server Authentication"
    ACCESS_CONTROL = "Access Control"
    RATE_LIMITING = "Rate Limiting"
    TRAFFIC_ENCRYPTION = "Traffic Encryption"
    ENCRYPTION_AT_REST = "Encryption at Rest"
