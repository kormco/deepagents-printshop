"""Optional LangSmith tracing for direct Anthropic SDK calls.

LangGraph nodes auto-trace when ``LANGCHAIN_TRACING_V2=true``. The bare
``anthropic.Anthropic()`` client does not — wrap it here so direct
``client.messages.create()`` calls also show up in the trace tree.

Tracing is fully opt-in. If ``LANGCHAIN_TRACING_V2`` is unset/false the
wrapper is a no-op and the client is returned unmodified, so call sites
can use ``maybe_wrap_anthropic`` unconditionally without paying a cost
when tracing is disabled. ``langsmith`` is imported lazily so an unused
install never pays the import cost either.
"""

from __future__ import annotations

import os
from typing import Any


def is_tracing_enabled() -> bool:
    """Return True if ``LANGCHAIN_TRACING_V2`` is set to a truthy value."""
    return os.environ.get("LANGCHAIN_TRACING_V2", "").strip().lower() in ("true", "1", "yes")


def maybe_wrap_anthropic(client: Any) -> Any:
    """Patch an Anthropic client for LangSmith tracing if enabled.

    No-op when tracing is disabled — returns ``client`` unchanged. Safe
    to call at every Anthropic client instantiation; the cost when
    disabled is one env-var lookup.
    """
    if not is_tracing_enabled():
        return client
    try:
        from langsmith.wrappers import wrap_anthropic  # lazy import
    except ImportError:
        # langsmith not installed — leave the client untouched.
        return client
    return wrap_anthropic(client)
