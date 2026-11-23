"""Fetchers, one per included source, behind one interface (:class:`base.Fetcher`)."""

from __future__ import annotations

from commonswire.fetchers.base import Fetcher
from commonswire.fetchers.wikinews import WikinewsFetcher
from commonswire.fetchers.wordpress import (
    LINGUA_FETCHERS,
    AltNewsFetcher,
    BalkanDiskursBosnianFetcher,
    BalkanDiskursFetcher,
    FactlyFetcher,
    GlobalVoicesFetcher,
    PublicRecordFetcher,
    ThreeSixtyInfoFetcher,
    WordPressFetcher,
)

FETCHERS: dict[str, type[Fetcher]] = {
    cls.source_id: cls
    for cls in (
        GlobalVoicesFetcher,
        WikinewsFetcher,
        ThreeSixtyInfoFetcher,
        PublicRecordFetcher,
        BalkanDiskursFetcher,
        BalkanDiskursBosnianFetcher,
        FactlyFetcher,
        AltNewsFetcher,
    )
}
#: The Global Voices language sites (series 0.3 on, under the Lingua rule).
FETCHERS.update(LINGUA_FETCHERS)

#: The sources collected through the WordPress REST API.
WORDPRESS: dict[str, type[WordPressFetcher]] = {
    k: v for k, v in FETCHERS.items() if issubclass(v, WordPressFetcher)
}
