from pathlib import Path
from types import SimpleNamespace

from auditlens import suggest
from auditlens.fixes import suggest_by_rules
from auditlens.loader import load_file

DATA = Path(__file__).resolve().parent.parent / "sample_data"


class FakeClient:
    """Stands in for the NVIDIA client so tests never touch the network."""

    def __init__(self, reply=None, error=None):
        self.reply, self.error = reply, error
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        if self.error:
            raise self.error
        message = SimpleNamespace(content=self.reply)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def messy():
    return load_file(DATA / "messy_sales.csv")


def test_valid_reply_is_used():
    reply = """```json
    [{"operation": "to_number", "column": "Amount", "description": "Make Amount numeric."},
     {"operation": "clean_headers", "column": "*", "description": "Trim header spaces."}]
    ```"""
    fixes = suggest.suggest_fixes(messy(), client=FakeClient(reply))
    assert [(f["operation"], f["column"]) for f in fixes] == [("to_number", " Amount "), ("clean_headers", "*")]
    assert fixes[0]["description"] == "Make Amount numeric."


def test_unknown_operations_columns_and_damaging_fixes_are_dropped():
    reply = """[{"operation": "delete_duplicates", "column": "*"},
               {"operation": "tidy_text", "column": "Not A Column"},
               {"operation": "to_number", "column": "Customer"},
               {"operation": "tidy_text", "column": "Customer", "description": "Our AI tidies names"}]"""
    fixes = suggest.suggest_fixes(messy(), client=FakeClient(reply))
    assert [(f["operation"], f["column"]) for f in fixes] == [("tidy_text", "Customer")]
    assert "AI" not in fixes[0]["description"]


def test_garbage_reply_falls_back_to_rules():
    df = messy()
    assert suggest.suggest_fixes(df, client=FakeClient("Sorry, I can't help.")) == suggest_by_rules(df)


def test_errors_fall_back_to_rules():
    df = messy()
    assert suggest.suggest_fixes(df, client=FakeClient(error=TimeoutError())) == suggest_by_rules(df)


def test_no_key_uses_rules(monkeypatch):
    monkeypatch.setattr(suggest, "get_api_key", lambda: None)
    df = messy()
    assert suggest.suggest_fixes(df) == suggest_by_rules(df)


def test_sample_sent_is_small():
    text = suggest.describe(messy())
    assert text.count("\nINV-") <= suggest.SAMPLE_ROWS
