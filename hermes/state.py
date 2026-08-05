IDLE = "IDLE"
ACTIVE = "ACTIVE"

# (current state, gesture) -> (new state, seconds it must be held)
TRANSITIONS = {
    (IDLE,   "open_palm"): (ACTIVE, 1.0),
    (ACTIVE, "fist"):      (IDLE,   1.0),
    (ACTIVE, "none"):      (IDLE,   3.0),
}


class StateMachine:
    def __init__(self) -> None:
        self.state = IDLE

    def update(self, gesture: str, held: float) -> str:
        found = TRANSITIONS.get((self.state, gesture))
        if found is not None:
            new_state, required = found
            if held >= required:
                self.state = new_state

        return self.state