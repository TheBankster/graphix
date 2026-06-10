from enum import Enum

class CONTROL(Enum):
    CLIENT_AUTHENTICATION = "Client Authentication"
    SERVER_AUTHENTICATION = "Server Authentication"
    ACCESS_CONTROL = "Access Control"
    RATE_LIMITING = "Rate Limiting"
    DATA_IN_TRANSIT_ENCRYPTION = "Data-in-transit Encryption"
    DATA_AT_REST_ENCRYPTION = "Data-at-rest Encryption"
