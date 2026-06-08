from enum import Enum

class CONTROL(Enum):
    CLIENT_AUTHENTICATION = "Client Authentication"
    SERVER_AUTHENTICATION = "Server Authentication"
    ACCESS_CONTROL = "Access Control"
    RATE_LIMITING = "Rate Limiting"
    TRAFFIC_ENCRYPTION = "Traffic Encryption"
