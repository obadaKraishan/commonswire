"""The Lingua link, versions and listing plan, with invented posts and pages. No network."""

from __future__ import annotations

import json

import pytest

from commonswire.lingua import (
    ENGLISH_NOT_RELEASED,
    NO_ENGLISH,
    EnglishIndex,
    ListingPlan,
    english_index,
    english_posts,
    english_version,
    fingerprint,
    link_posts,
    page_versions,
    plan_for,
    read_links,
    same_post,
    version_groups,
    write_links,
)
from commonswire.listingbylines import Story, learn_labels, listing_markup
from commonswire.schema import canonical_url

GV = "https://globalvoices.org"


def body(*links, images=()):
    a = "".join(f'<p>Invented words <a href="{u}">a link</a>.</p>' for u in links)
    img = "".join(f'<img src="{u}" alt="">' for u in images)
    return f"<div>{a}{img}</div>"


def post(link, html, pid=1, date="2020-01-01T00:00:00"):
    return {"id": pid, "link": link, "date_gmt": date, "content": {"rendered": html}}


EN_A = f"{GV}/2020/01/01/an-invented-story/"
EN_B = f"{GV}/2020/02/02/another-invented-story/"
LINKS_A = [f"https://example{i}.org/page-{i}" for i in range(6)]
LINKS_B = [f"https://example{i}.net/other-{i}" for i in range(6)]


def test_fingerprint_keeps_other_sites_english_articles_and_image_names():
    html = body(
        "https://www.Example.org/a/",
        "//example.com/b",
        f"{GV}/2019/05/05/an-old-story/",
        "https://fr.globalvoices.org/2019/05/05/une-histoire/",
        f"{GV}/author/someone/",
        "mailto:x@example.org",
        images=[f"{GV}/wp-content/uploads/2020/01/invented-photo-800x600.jpg"],
    )
    parts = fingerprint(html)
    assert "a:example.org/a" in parts
    assert "a:example.com/b" in parts
    assert "gv:/2019/05/05/an-old-story" in parts
    assert "i:invented-photo.jpg" in parts
    assert not any("fr.globalvoices" in p or "author" in p for p in parts)
    assert len(parts) == 4


def index_of(*posts):
    return english_index(posts)


def test_a_translation_is_matched_to_the_english_post_it_shares_its_links_with():
    index = index_of(post(EN_A, body(*LINKS_A)), post(EN_B, body(*LINKS_B), pid=2))
    m = index.match(fingerprint(body(*LINKS_A[:5], "https://example.fr/x")))
    assert m is not None and m.url == EN_A and m.shared == 5 and m.runner_up == 0
    assert m.jaccard == pytest.approx(5 / 7, abs=1e-4)


def test_too_few_shared_parts_or_a_close_runner_up_is_no_match():
    index = index_of(post(EN_A, body(*LINKS_A)), post(EN_B, body(*LINKS_A[:4]), pid=2))
    # two shared parts only
    assert index.match(fingerprint(body(*LINKS_A[:2]))) is None
    # both English posts share four parts: no clear lead
    assert index.match(fingerprint(body(*LINKS_A[:4]))) is None
    # a low share of the two bodies together
    many = [f"https://filler{i}.org/" for i in range(30)]
    assert index.match(fingerprint(body(*LINKS_A[4:6], *LINKS_A[:1], *many))) is None


def test_parts_found_in_many_english_posts_are_not_used():
    common = "https://donate.example.org/"
    posts = [post(f"{GV}/2020/03/{i:02d}/story-{i}/", body(common), pid=i) for i in range(1, 45)]
    index = index_of(*posts)
    assert "a:donate.example.org" not in index.posts
    assert index.candidates(fingerprint(body(common))) == []


def test_a_later_answer_for_the_same_post_replaces_the_earlier_one():
    index = index_of(post(EN_A, body(*LINKS_B)), post(EN_A, body(*LINKS_A)))
    assert len(index) == 1
    assert index.match(fingerprint(body(*LINKS_A))).url == EN_A


def test_link_posts_counts_matches_misses_and_bodies_too_bare_to_match():
    index = index_of(post(EN_A, body(*LINKS_A)))
    lingua = [
        post("https://fr.globalvoices.org/2020/01/05/une-histoire/", body(*LINKS_A[:5])),
        post("https://fr.globalvoices.org/2020/01/06/une-autre/", body(*LINKS_B), pid=2),
        post("https://fr.globalvoices.org/2020/01/07/courte/", body(LINKS_A[0]), pid=3),
        {"id": 4, "link": "not an address", "content": {"rendered": ""}},
    ]
    links, st = link_posts("globalvoices_fr", lingua, index)
    assert (st.posts, st.matched, st.no_match, st.no_parts) == (3, 1, 1, 1)
    key = canonical_url("https://fr.globalvoices.org/2020/01/05/une-histoire/")
    assert links[key]["en"] == EN_A
    assert links[key]["url"].endswith("/une-histoire/")
    assert st.summary()["english_posts_indexed"] == 1


def test_links_are_written_and_read_back(tmp_path):
    path = tmp_path / "x" / "globalvoices_fr.links.json"
    write_links(path, {"b": {"en": EN_A}, "a": {"en": EN_B}})
    assert list(read_links(path)) == ["a", "b"]
    assert read_links(tmp_path / "missing.json") == {}


def test_page_versions_reads_the_pages_own_list():
    html = f"""<div class='translation-listing-container'><span class='translations-description'>
      Read in</span> <span class='translation-language post-translation-en'><a href="{EN_A}"
      title='x'>English</a></span><span class='translation-language post-translation-es'>
      <a href='https://es.globalvoices.org/2020/01/03/una-historia/'>Español</a></span>
      <span class='translation-language post-translation-fr'><a href='not a url'>x</a></span>
      </div>"""
    assert page_versions(html) == {
        "en": canonical_url(EN_A),
        "es": "https://es.globalvoices.org/2020/01/03/una-historia",
    }


def test_same_post_allows_another_date_but_the_same_slug():
    assert same_post(EN_A, EN_A)
    assert same_post(f"{GV}/2020/01/01/x-y", f"{GV}/2020/01/02/x-y")
    assert not same_post(f"{GV}/2020/01/01/x-y", f"{GV}/2020/01/01/x-z")
    assert not same_post(f"{GV}/2020/01/01/123", f"{GV}/2020/01/02/123")
    assert not same_post(f"{GV}/2020/01/01/x-y", "https://fr.globalvoices.org/2020/01/01/x-y")


def test_version_groups_link_the_editions_through_their_english_post():
    fr = "https://fr.globalvoices.org/2020/01/05/une-histoire/"
    es = "https://es.globalvoices.org/2020/01/06/una-historia/"
    out = version_groups(
        {fr: EN_A, es: EN_A}, {canonical_url(fr): ("T",), canonical_url(es): ("U",)}
    )
    assert out[canonical_url(EN_A)].other_versions == tuple(sorted((es, fr)))
    assert out[canonical_url(EN_A)].original_url == ""
    # only the English version credits no translator: it is the others' original
    assert out[canonical_url(fr)].original_url == EN_A
    assert set(out[canonical_url(fr)].other_versions) == {EN_A, es}


def test_version_groups_set_no_original_when_two_versions_credit_no_translator():
    fr = "https://fr.globalvoices.org/2020/01/05/une-histoire/"
    out = version_groups({fr: EN_A}, {})
    assert out[canonical_url(fr)].original_url == ""
    assert out[canonical_url(EN_A)].original_url == ""


def test_version_groups_may_name_a_lingua_original():
    es = "https://es.globalvoices.org/2020/01/06/una-historia/"
    out = version_groups({es: EN_A}, {canonical_url(EN_A): ("T",)})
    assert out[canonical_url(EN_A)].original_url == es
    assert out[canonical_url(es)].original_url == ""


def test_english_version_needs_exactly_one_english_address():
    assert english_version([EN_A, "https://fr.globalvoices.org/x"]) == EN_A
    assert english_version(["https://fr.globalvoices.org/x"]) == ""
    assert english_version([EN_A, EN_B]) == ""


def test_the_hold_reasons_have_no_colon():
    # the manifest counts a hold reason by its words before the first colon
    assert ":" not in NO_ENGLISH and ":" not in ENGLISH_NOT_RELEASED


def urls(n):
    return [f"https://fr.globalvoices.org/2020/01/{i:02d}/p{i}" for i in range(n)]


def test_the_plan_skips_pages_with_no_releasable_story_and_resyncs():
    order = urls(100)
    releasable = {order[5], order[95]}
    plan = ListingPlan(order, releasable, per_page=10, margin=1)
    assert plan.wanted(1) and plan.wanted(2)
    plan.observe(1, order[0:12])  # page 1 shows featured stories too
    plan.observe(2, order[12:22])
    assert plan.next_start == 22 and plan.per_page == 10
    assert not plan.wanted(3)
    plan.skipped()
    assert plan.next_start == 32
    for _ in range(5):
        plan.skipped()
    assert plan.next_start == 82
    assert not plan.wanted(9)  # 82..92, widened by one to 81..93: nothing releasable
    plan.next_start = 86
    assert plan.wanted(9)  # 85..97 holds 95
    plan.observe(9, order[86:96])
    assert plan.next_start == 96 and not plan.done()
    plan.observe(10, [])
    assert plan.done()


def test_plan_for_reads_the_run_the_links_and_the_english_rows(tmp_path):
    root = tmp_path
    run = root / "data" / "raw" / "backfill" / "globalvoices_fr" / "R"
    run.mkdir(parents=True)
    fr_a = "https://fr.globalvoices.org/2020/01/05/a/"
    fr_b = "https://fr.globalvoices.org/2020/01/06/b/"
    (run / "posts-p00001.json").write_text(
        json.dumps(
            [post(fr_a, "", 1, "2020-01-05T00:00:00"), post(fr_b, "", 2, "2020-01-06T00:00:00")]
        )
    )
    with pytest.raises(FileNotFoundError):
        plan_for(root, "globalvoices_fr", "R")
    write_links(
        root / "data" / "interim" / "lingua" / "globalvoices_fr.links.json",
        {
            canonical_url(fr_a): {"url": fr_a, "en": EN_A},
            canonical_url(fr_b): {"url": fr_b, "en": EN_B},
        },
    )
    rows = root / "data" / "interim" / "rows" / "globalvoices.jsonl"
    rows.parent.mkdir(parents=True)
    rows.write_text(
        json.dumps({"url": EN_A, "releasable": True, "status": "live"})
        + "\n"
        + json.dumps({"url": EN_B, "releasable": False, "status": "live"})
        + "\n"
    )
    plan, counts = plan_for(root, "globalvoices_fr", "R")
    assert counts == {"posts": 2, "releasable": 1}
    assert plan.flags == [False, True]  # newest first: b (held English), then a


def test_english_posts_read_backfills_then_update_caches(tmp_path):
    raw = tmp_path / "data" / "raw"
    bf = raw / "backfill" / "globalvoices" / "R"
    bf.mkdir(parents=True)
    (bf / "posts-p00001.json").write_text(json.dumps([post(EN_A, body(*LINKS_B))]))
    cache = raw / "update" / "U" / "cache"
    cache.mkdir(parents=True)
    (cache / "k1.json").write_text(
        json.dumps({"url": f"{GV}/wp-json/wp/v2/posts?x=1", "status": 200})
    )
    (cache / "k1.body").write_text(json.dumps([post(EN_A, body(*LINKS_A))]))
    (cache / "k2.json").write_text(
        json.dumps({"url": "https://fr.globalvoices.org/wp-json/wp/v2/posts", "status": 200})
    )
    (cache / "k3.json").write_text(
        json.dumps({"url": f"{GV}/wp-json/wp/v2/posts?y=1", "status": 404})
    )
    (cache / "k4.json").write_text("not json")
    got = list(english_posts(tmp_path))
    assert len(got) == 2
    assert english_index(got).match(fingerprint(body(*LINKS_A))).url == EN_A


def test_the_index_is_independent_of_the_order_of_ties():
    a = EnglishIndex(
        [("b", "B", frozenset({"x", "y", "z"})), ("a", "A", frozenset({"x", "y", "z"}))]
    )
    assert [c[0] for c in a.candidates(frozenset({"x", "y", "z"}))] == ["a", "b"]


def test_lingua_listing_learns_its_labels_from_stories_with_two_blocks():
    markup = listing_markup("globalvoices_fr")
    assert markup.url == "https://fr.globalvoices.org/page/{page}/"
    assert markup.writer_labels == ()
    stories = [
        Story("u1", {"écrit par": ["A"], "traduit par": ["B"]}),
        Story("u2", {"écrit par": ["C"]}),
        Story("u3", {"écrit par": ["D"], "traduit par": ["E"]}),
    ]
    learned = learn_labels(stories, markup)
    assert learned.writer_labels == ("écrit par",)
    assert learned.translator_labels == ("traduit par",)
    assert learn_labels([Story("u", {"x": ["A"]})], markup) is markup
    assert learn_labels(stories, listing_markup("globalvoices")) is listing_markup("globalvoices")
    with pytest.raises(KeyError):
        listing_markup("factly")


# ---- the rule in the release ----

from datetime import datetime, timezone  # noqa: E402

from commonswire import release as rel  # noqa: E402
from commonswire.release import ReleaseError, collect  # noqa: E402
from commonswire.schema import make_article  # noqa: E402
from commonswire.sources import load_sources, render_credit  # noqa: E402
from test_sources import row, write_csv  # noqa: E402

CREDIT = "This story by {authors} originally appeared on {source}: {title} ({url}), {license}"
WORDS = "Invented words about an invented council and an invented bridge, {n} times over. "


def gv_registry(tmp_path, english=True):
    rows = []
    if english:
        rows.append(
            row(
                source_id="globalvoices",
                name="Global Voices",
                homepage=f"{GV}/",
                license="CC-BY-3.0",
                credit_line=CREDIT,
            )
        )
    rows.append(
        row(
            source_id="globalvoices_fr",
            name="Global Voices (fr)",
            homepage="https://fr.globalvoices.org/",
            languages="fr",
            edition_of="globalvoices",
            license="CC-BY-3.0",
            credit_line=CREDIT,
            reason_code="released_with_english",
            third_party_rule="released only when its English version is a released row",
        )
    )
    if not english:
        rows.append(row(source_id="globalvoices", name="Global Voices", homepage=f"{GV}/"))
    return load_sources(write_csv(tmp_path, rows))


def gv_row(source, url, n, *, versions=(), releasable=True, lang="en"):
    name = "Global Voices" if source == "globalvoices" else "Global Voices (fr)"
    a = make_article(
        source_id=source,
        url=url,
        title=f"Invented story {n}",
        text=WORDS.format(n=n) * (n + 3),
        published_at=datetime(2020, 1, n, tzinfo=timezone.utc),
        retrieved_at=datetime(2026, 11, 1, tzinfo=timezone.utc),
        language=lang,
        license="CC-BY-3.0",
        credit_line=render_credit(
            CREDIT,
            title=f"Invented story {n}",
            authors=("A",),
            source=name,
            url=url,
            license="CC-BY-3.0",
        ),
        authors=("A",),
        releasable=releasable,
        hold_reason="" if releasable else "no byline: Global Voices asks for the author's name",
        other_versions=tuple(versions),
    )
    return json.loads(a.model_dump_json())


def test_a_lingua_row_is_released_only_with_its_released_english_version(tmp_path, monkeypatch):
    monkeypatch.setitem(rel.SERIES, (9, 8), ("globalvoices", "globalvoices_fr"))
    fr = [f"https://fr.globalvoices.org/2020/01/0{i}/histoire-{i}/" for i in (1, 2, 3)]
    rows = {
        "globalvoices": [
            gv_row("globalvoices", EN_A, 1, versions=[fr[0]]),
            gv_row("globalvoices", EN_B, 2, versions=[fr[1]], releasable=False),
        ],
        "globalvoices_fr": [
            gv_row("globalvoices_fr", fr[0], 4, versions=[EN_A], lang="fr"),
            gv_row("globalvoices_fr", fr[1], 5, versions=[EN_B], lang="fr"),
            gv_row("globalvoices_fr", fr[2], 6, lang="fr"),
        ],
    }
    r = collect(tmp_path, "9.8.0", gv_registry(tmp_path), rows=rows)
    assert r.checks.ok
    released = {x["url"] for x in r.rows["by"]}
    assert released == {EN_A, fr[0]}
    assert dict(r.checks.held) == {"globalvoices": 1, "globalvoices_fr": 2}
    assert r.checks.held_reasons[ENGLISH_NOT_RELEASED] == 1
    assert r.checks.held_reasons[NO_ENGLISH] == 1
    got = next(x for x in r.rows["by"] if x["url"] == fr[0])
    assert got["other_versions"] == [EN_A] and got["language"] == "fr"


def test_a_lingua_edition_needs_the_english_site_in_its_series(tmp_path, monkeypatch):
    monkeypatch.setitem(rel.SERIES, (9, 8), ("globalvoices_fr",))
    with pytest.raises(ReleaseError, match="released only with their English versions"):
        collect(tmp_path, "9.8.0", gv_registry(tmp_path), rows={"globalvoices_fr": []})


def test_current_address_moves_the_old_domain():
    from commonswire.lingua import current_address

    assert current_address("https://globalvoicesonline.org/2008/01/01/x/") == f"{GV}/2008/01/01/x/"
    assert (
        current_address("http://fr.globalvoicesonline.org/2008/01/01/1/")
        == "http://fr.globalvoices.org/2008/01/01/1/"
    )
    assert current_address(EN_A) == EN_A
    html = """<span class='translation-language post-translation-en'><a
      href="https://globalvoicesonline.org/2008/01/01/x/">x</a></span>"""
    assert page_versions(html) == {"en": f"{GV}/2008/01/01/x"}


# ---- the weekly route ----

from commonswire.lingua import (  # noqa: E402
    WeeklyLinks,
    add_new_versions,
    hreflang_new_versions,
    link_new_posts,
)


class _Resp:
    def __init__(self, status, text=""):
        self.status, self.text = status, text


class _Client:
    def __init__(self, pages):
        self.pages, self.calls = pages, []

    def get(self, url, *, accept, note, log_as):
        self.calls.append((url, log_as))
        return _Resp(*self.pages.get(url, (404, "")))


class _Fetcher:
    source_id = "globalvoices_fr"

    def __init__(self):
        self.versions = {}


def test_new_lingua_posts_are_linked_by_fingerprint_or_their_own_page():
    fr_a = "https://fr.globalvoices.org/2026/11/20/a/"
    fr_b = "https://fr.globalvoices.org/2026/11/21/b/"
    fr_c = "https://fr.globalvoices.org/2026/11/22/c/"
    fr_old = "https://fr.globalvoices.org/2026/11/01/old/"
    ctx = WeeklyLinks(
        english_posts=[post(EN_A, body(*LINKS_A))],
        english_rows={canonical_url(EN_A): EN_A, canonical_url(EN_B): EN_B},
    )
    page_b = """<span class='translation-language post-translation-en'><a
      href="https://globalvoicesonline.org/2020/02/03/another-invented-story/">x</a></span>"""
    client = _Client({fr_b: (200, page_b), fr_c: (200, "<p>no list</p>")})
    f = _Fetcher()
    posts = [
        post(fr_a, body(*LINKS_A[:5])),
        post(fr_b, body(LINKS_B[0])),
        post(fr_c, ""),
        post(fr_old, body(*LINKS_A)),
    ]
    counts = link_new_posts(f, client, posts, {fr_old: "cw_x"}, ctx)
    assert counts == {
        "by_fingerprint": 1,
        "by_page": 1,
        "new_posts": 3,
        "no_english_version": 1,
        "page_names_no_english_row": 1,
        "pages_read": 2,
    }
    assert f.versions[canonical_url(fr_a)]["other_versions"] == [EN_A]
    # an old address under another date names the same English row
    assert f.versions[canonical_url(fr_b)]["other_versions"] == [EN_B]
    assert canonical_url(fr_c) not in f.versions
    assert all(log_as.startswith("cw_") for _, log_as in client.calls)
    # the page cap
    f2 = _Fetcher()
    capped = link_new_posts(f2, _Client({}), posts[1:3], {}, ctx, max_pages=1)
    assert capped["pages_read"] == 1 and capped["no_english_version"] == 2


def _row(url, sid, rid, versions=(), translators=(), original=""):
    return {
        "id": rid,
        "source_id": sid,
        "url": url,
        "other_versions": list(versions),
        "translators": list(translators),
        "original_url": original,
    }


def test_a_new_lingua_row_joins_its_english_group():
    fr = "https://fr.globalvoices.org/2026/11/20/a/"
    es = "https://es.globalvoices.org/2026/11/19/a/"
    merged = {
        "globalvoices": {"e": _row(EN_A, "globalvoices", "e", [es])},
        "globalvoices_es": {"s": _row(es, "globalvoices_es", "s", [EN_A], ["T"], EN_A)},
        "globalvoices_fr": {"f": _row(fr, "globalvoices_fr", "f", [EN_A], ["U"])},
    }
    assert add_new_versions(merged, ["f"]) == 3
    assert merged["globalvoices"]["e"]["other_versions"] == sorted([es, fr])
    assert merged["globalvoices_es"]["s"]["other_versions"] == sorted([EN_A, fr])
    assert merged["globalvoices_fr"]["f"]["other_versions"] == sorted([EN_A, es])
    # every member is a row: the one crediting no translator (English) is the original
    assert merged["globalvoices_fr"]["f"]["original_url"] == EN_A
    assert merged["globalvoices"]["e"]["original_url"] == ""
    assert add_new_versions(merged, ["f"]) == 0  # nothing more to add


def test_a_group_with_a_member_that_is_not_a_row_keeps_its_original():
    fr = "https://fr.globalvoices.org/2026/11/20/a/"
    held = "https://de.globalvoices.org/2026/11/18/a/"
    merged = {
        "globalvoices": {"e": _row(EN_A, "globalvoices", "e", [held], original="")},
        "globalvoices_fr": {"f": _row(fr, "globalvoices_fr", "f", [EN_A], ["U"])},
    }
    add_new_versions(merged, ["f"])
    assert merged["globalvoices_fr"]["f"]["other_versions"] == sorted([EN_A, held])
    assert merged["globalvoices_fr"]["f"]["original_url"] == ""  # no original known
    merged["globalvoices"]["e"]["original_url"] = held  # the English is a translation
    merged["globalvoices_fr"]["f"]["other_versions"] = [EN_A]
    add_new_versions(merged, ["f"])
    assert merged["globalvoices_fr"]["f"]["original_url"] == held


def test_a_row_with_no_english_version_is_left_alone():
    fr = "https://fr.globalvoices.org/2026/11/20/a/"
    merged = {"globalvoices_fr": {"f": _row(fr, "globalvoices_fr", "f")}}
    assert add_new_versions(merged, ["f"]) == 0


def test_hreflang_pairs_reach_both_rows():
    bs = "https://balkandiskurs.com/prica/"
    en = "https://balkandiskurs.com/en/story/"
    html = f"""<head><link rel="alternate" hreflang="bs" href="{bs}">
      <link rel="alternate" hreflang="en" href="{en}"></head>"""
    merged = {
        "balkandiskurs": {"a": _row(en, "balkandiskurs", "a")},
        "balkandiskurs_bs": {"b": _row(bs, "balkandiskurs_bs", "b")},
    }
    assert hreflang_new_versions(merged, [html], ["balkandiskurs", "balkandiskurs_bs"]) == 2
    assert merged["balkandiskurs"]["a"]["other_versions"] == [bs]
    assert merged["balkandiskurs_bs"]["b"]["other_versions"] == [en]


def test_the_card_names_the_license_versions_and_languages_the_rows_carry():
    from collections import Counter

    from commonswire.release_text import CONFIG_TEXT, config_text, language_tags

    rows = [{"license": x} for x in ("CC-BY-4.0", "CC-BY-2.0", "CC-BY-2.5", "CC-BY-3.0")]
    assert config_text("by", rows) == "Creative Commons Attribution (CC BY 2.0, 2.5, 3.0 and 4.0)"
    # the published series' text is what the rows give
    old = [{"license": x} for x in ("CC-BY-2.5", "CC-BY-3.0", "CC-BY-4.0")]
    assert config_text("by", old) == CONFIG_TEXT["by"]
    assert config_text("by-sa", [{"license": "CC-BY-SA-4.0"}]) == CONFIG_TEXT["by-sa"]
    assert config_text("pd", []) == CONFIG_TEXT["pd"]
    assert config_text("by", []) == CONFIG_TEXT["by"]
    langs = Counter({"fr": 3, "en": 9, "zh-Hant": 1, "zh-Hans": 2, "bs": 4})
    assert language_tags(langs) == ["en", "bs", "fr", "zh"]
    assert language_tags(Counter({"en": 5})) == ["en"]


def test_the_card_explains_rows_held_by_the_lingua_rule(tmp_path, monkeypatch):
    from commonswire.release_text import card

    monkeypatch.setitem(rel.SERIES, (9, 8), ("globalvoices", "globalvoices_fr"))
    fr = [f"https://fr.globalvoices.org/2020/01/0{i}/histoire-{i}/" for i in (1, 2, 3)]
    rows = {
        "globalvoices": [
            gv_row("globalvoices", EN_A, 1, versions=[fr[0]]),
            gv_row("globalvoices", EN_B, 2, versions=[fr[1]], releasable=False),
        ],
        "globalvoices_fr": [
            gv_row("globalvoices_fr", fr[0], 4, versions=[EN_A], lang="fr"),
            gv_row("globalvoices_fr", fr[1], 5, versions=[EN_B], lang="fr"),
            gv_row("globalvoices_fr", fr[2], 6, lang="fr"),
        ],
    }
    reg = gv_registry(tmp_path)
    r = collect(tmp_path, "9.8.0", reg, rows=rows)
    text = card(r, reg, 0)
    assert "language:\n- en\n- fr\n" in text
    assert "2 rows of Global Voices' language sites are held back by the Lingua rule" in text
    assert "1 more rows are held back because the source asks for the author's name" in text
    assert "a BCP 47 tag" in text
