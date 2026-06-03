Tracing: bool = False

def trace(str) -> None:
    global Tracing
    if Tracing:
        print(str)
