"""Fetchers, one per included source, behind one interface (:class:`base.Fetcher`)."""

from __future__ import annotations

from commonswire.fetchers.base import Fetcher
from commonswire.fetchers.wikinews import WikinewsFetcher
from commonswire.fetchers.wordpress import GlobalVoicesFetcher

FETCHERS: dict[str, type[Fetcher]] = {
    GlobalVoicesFetcher.source_id: GlobalVoicesFetcher,
    WikinewsFetcher.source_id: WikinewsFetcher,
}
