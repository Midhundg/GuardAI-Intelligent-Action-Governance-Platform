class TraceEngine:

    def __init__(self):
        self.steps = []

    def add(self, message: str):
        self.steps.append(message)

    def get_trace(self):
        return self.steps