from pathlib import Path


class RVCModelService:
    ALLOWED_SUFFIXES = {".pth", ".onnx", ".zip"}

    def validate_model_file(self, path: str) -> dict:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(path)
        if p.suffix.lower() not in self.ALLOWED_SUFFIXES:
            raise ValueError("RVC model must be .pth, .onnx, or .zip")
        return {"path": str(p), "size_bytes": p.stat().st_size, "valid": True}
