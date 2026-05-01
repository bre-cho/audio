class FormantPreservation:
    def build_config(self, enabled: bool = True, strength: float = 0.8) -> dict:
        return {"enabled": enabled, "strength": max(0.0, min(1.0, strength))}
