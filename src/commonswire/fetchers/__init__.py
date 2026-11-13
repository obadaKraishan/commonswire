"""Fetchers, one per included source, behind one interface (:class:`base.Fetcher`)."""

from __future__ import annotations

from commonswire.fetchers.base import Fetcher
from commonswire.fetchers.wikinews import WikinewsFetcher
from commonswire.fetchers.wordpress import (
    AltNewsFetcher,
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
        FactlyFetcher,
        AltNewsFetcher,
    )
}

#: The sources collected through the WordPress REST API.
WORDPRESS: dict[str, type[WordPressFetcher]] = {
    k: v for k, v in FETCHERS.items() if issubclass(v, WordPressFetcher)
}
