"""Tests for tools.tracing — opt-in LangSmith wrapping for Anthropic clients."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools import tracing  # noqa: E402


class TestIsTracingEnabled:
    def test_unset_is_disabled(self, monkeypatch):
        monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)
        assert tracing.is_tracing_enabled() is False

    def test_empty_is_disabled(self, monkeypatch):
        monkeypatch.setenv("LANGCHAIN_TRACING_V2", "")
        assert tracing.is_tracing_enabled() is False

    def test_false_is_disabled(self, monkeypatch):
        monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")
        assert tracing.is_tracing_enabled() is False

    def test_true_is_enabled(self, monkeypatch):
        monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")
        assert tracing.is_tracing_enabled() is True

    def test_true_uppercase(self, monkeypatch):
        monkeypatch.setenv("LANGCHAIN_TRACING_V2", "TRUE")
        assert tracing.is_tracing_enabled() is True

    def test_one_is_enabled(self, monkeypatch):
        monkeypatch.setenv("LANGCHAIN_TRACING_V2", "1")
        assert tracing.is_tracing_enabled() is True


class TestMaybeWrapAnthropic:
    def test_no_op_when_disabled(self, monkeypatch):
        """The whole point: zero-cost pass-through when tracing is off."""
        monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)
        sentinel = object()
        assert tracing.maybe_wrap_anthropic(sentinel) is sentinel

    def test_wraps_when_enabled(self, monkeypatch):
        """When tracing is on, wrap_anthropic gets called and we return its result."""
        monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")

        # Inject a fake langsmith.wrappers module so this test doesn't depend on
        # whether the real package is installed in the test environment.
        import types

        wrapped_marker = object()

        def fake_wrap(client):
            assert client is sentinel
            return wrapped_marker

        fake_wrappers = types.ModuleType("langsmith.wrappers")
        fake_wrappers.wrap_anthropic = fake_wrap
        fake_langsmith = types.ModuleType("langsmith")
        fake_langsmith.wrappers = fake_wrappers

        monkeypatch.setitem(sys.modules, "langsmith", fake_langsmith)
        monkeypatch.setitem(sys.modules, "langsmith.wrappers", fake_wrappers)

        sentinel = object()
        assert tracing.maybe_wrap_anthropic(sentinel) is wrapped_marker

    def test_falls_back_when_langsmith_missing(self, monkeypatch):
        """If tracing is enabled but langsmith isn't installed, return the client unchanged."""
        monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")

        # Force the import to fail by inserting a sentinel that raises on attribute access.
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "langsmith.wrappers" or name.startswith("langsmith"):
                raise ImportError("simulated missing langsmith")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        sentinel = object()
        assert tracing.maybe_wrap_anthropic(sentinel) is sentinel
