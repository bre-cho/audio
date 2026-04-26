from __future__ import annotations

from pathlib import Path

from app.audio_factory import schema_migration as sm
from app.core.storage import StoredObject
from app.services.object_storage import upload_file_to_object_storage
from app.utils.script_parser import parse_speaker_script
from app.utils.text_normalizer import normalize_text


def test_parse_speaker_script_skips_invalid_lines_and_trims_values() -> None:
    raw = """
    Alice: hello
    invalid line
    Bob:   hi there
      : missing speaker
    """

    parsed = parse_speaker_script(raw)

    assert parsed == [
        {"speaker": "Alice", "text": "hello"},
        {"speaker": "Bob", "text": "hi there"},
        {"speaker": "", "text": "missing speaker"},
    ]


def test_normalize_text_collapses_whitespace() -> None:
    assert normalize_text("  hello\n\tworld   from   audio  ") == "hello world from audio"


def test_upload_file_to_object_storage_reads_file_and_delegates(monkeypatch, tmp_path: Path) -> None:
    local = tmp_path / "sample.bin"
    local.write_bytes(b"abc123")

    calls: list[tuple[str, bytes, str]] = []

    class _FakeStorageService:
        def put_bytes(self, key: str, data: bytes, content_type: str) -> StoredObject:
            calls.append((key, data, content_type))
            return StoredObject(key=key, public_url=f"/artifacts/{key}", size_bytes=len(data), checksum="x" * 64)

    monkeypatch.setattr("app.services.object_storage.StorageService", _FakeStorageService)

    stored = upload_file_to_object_storage(
        local_path=str(local),
        key="unit/sample.bin",
        content_type="application/octet-stream",
    )

    assert stored.key == "unit/sample.bin"
    assert calls == [("unit/sample.bin", b"abc123", "application/octet-stream")]


def test_ensure_column_executes_alter_when_column_missing(monkeypatch) -> None:
    class _Inspector:
        @staticmethod
        def get_columns(_table_name: str) -> list[dict[str, str]]:
            return [{"name": "id"}]

    class _Conn:
        def __init__(self) -> None:
            self.statements: list[str] = []

        def execute(self, stmt) -> None:
            self.statements.append(str(stmt))

    conn = _Conn()
    monkeypatch.setattr(sm, "inspect", lambda _conn: _Inspector())

    sm._ensure_column(conn, "audio_jobs", "workflow_type", "workflow_type VARCHAR(50)")

    assert any("ALTER TABLE audio_jobs ADD COLUMN workflow_type VARCHAR(50)" in sql for sql in conn.statements)


def test_ensure_audio_outputs_index_executes_create_when_missing(monkeypatch) -> None:
    class _Inspector:
        @staticmethod
        def get_indexes(_table_name: str) -> list[dict[str, str]]:
            return []

    class _Conn:
        def __init__(self) -> None:
            self.statements: list[str] = []

        def execute(self, stmt) -> None:
            self.statements.append(str(stmt))

    conn = _Conn()
    monkeypatch.setattr(sm, "inspect", lambda _conn: _Inspector())

    sm._ensure_audio_outputs_index(conn, "ix_audio_outputs_artifact_id", "CREATE INDEX ix_audio_outputs_artifact_id ON audio_outputs (artifact_id)")

    assert any("CREATE INDEX ix_audio_outputs_artifact_id" in sql for sql in conn.statements)


def test_apply_audio_factory_schema_invokes_expected_steps(monkeypatch) -> None:
    ensure_column_calls: list[tuple[str, str]] = []
    ensure_index_calls: list[str] = []
    executed_sql: list[str] = []
    created_with: list[object] = []

    class _Conn:
        def execute(self, stmt) -> None:
            executed_sql.append(str(stmt))

    class _BeginCtx:
        def __init__(self, conn: _Conn) -> None:
            self.conn = conn

        def __enter__(self) -> _Conn:
            return self.conn

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

    class _Engine:
        def __init__(self) -> None:
            self.conn = _Conn()

        def begin(self) -> _BeginCtx:
            return _BeginCtx(self.conn)

    def _fake_ensure_column(_conn, table_name: str, column_name: str, _ddl: str) -> None:
        ensure_column_calls.append((table_name, column_name))

    def _fake_ensure_index(_conn, index_name: str, _ddl: str) -> None:
        ensure_index_calls.append(index_name)

    monkeypatch.setattr(sm, "_ensure_column", _fake_ensure_column)
    monkeypatch.setattr(sm, "_ensure_audio_outputs_index", _fake_ensure_index)
    monkeypatch.setattr(sm.Base.metadata, "create_all", lambda bind: created_with.append(bind))

    engine = _Engine()
    sm.apply_audio_factory_schema(engine)

    assert created_with == [engine]
    assert ("audio_jobs", "workflow_type") in ensure_column_calls
    assert ("audio_outputs", "artifact_id") in ensure_column_calls
    assert "ix_audio_outputs_artifact_id" in ensure_index_calls
    assert any("UPDATE audio_jobs SET workflow_type = job_type" in sql for sql in executed_sql)
    assert any("UPDATE audio_outputs SET source_job_id = job_id" in sql for sql in executed_sql)