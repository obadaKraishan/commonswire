from __future__ import annotations

from commonswire.html import article_text, has_markup, links, page_text, strip_tags

BODY = """
<div class="entry">
  <p>First   paragraph with <a href="/x">a link</a>&nbsp;and an <em>emphasis</em>.</p>
  <figure><img src="a.jpg"><figcaption>A caption that must go.</figcaption></figure>
  <p>Second paragraph.<br>Same paragraph after a break.</p>
  <script>var x = 1;</script>
  <div class="share-box"><p>Share this story</p></div>
  <iframe src="https://video.example"></iframe>
  <aside><p>Related: another story</p></aside>
  <blockquote><p>A quoted line.</p></blockquote>
  <ul><li>One</li><li>Two</li></ul>
</div>
"""


def test_article_text_keeps_words_and_drops_media_captions_scripts_and_furniture():
    text = article_text(BODY, drop_classes=["share-box"])
    assert text.split("\n\n") == [
        "First paragraph with a link and an emphasis.",
        "Second paragraph.",
        "Same paragraph after a break.",
        "A quoted line.",
        "One",
        "Two",
    ]
    assert "caption" not in text and "var x" not in text and "Share" not in text


def test_page_text_keeps_footers_and_navigation():
    html = "<html><head><title>T</title></head><body><nav>Menu</nav><p>Body</p>"
    html += "<footer>Licensed under CC BY 4.0</footer></body></html>"
    assert page_text(html).splitlines() == ["Menu", "Body", "Licensed under CC BY 4.0"]


def test_sloppy_html_does_not_swallow_the_rest_of_the_page():
    html = "<figure><span>caption<p>still in figure</figure><p>After</p>"
    assert article_text(html) == "After"


def test_drop_classes_match_ids_and_roles_too():
    html = '<div id="newsletter-signup"><p>Sign up</p></div><p>Kept</p>'
    assert article_text(html, drop_classes=["newsletter"]) == "Kept"


def test_strip_tags_and_has_markup():
    assert strip_tags("<b>Big</b> &amp; <i>bold</i>") == "Big & bold"
    assert has_markup("text <p>with</p> tags")
    assert not has_markup("5 < 6 and 7 > 3")


def test_links_include_rel_license_and_anchor_text():
    html = '<head><link rel="license" href="https://creativecommons.org/licenses/by/4.0/"></head>'
    html += '<a href="/republish">Republish <b>our</b> stories</a><a>no href</a>'
    assert links(html) == [
        ("https://creativecommons.org/licenses/by/4.0/", "rel=license"),
        ("/republish", "Republish our stories"),
        ("", "no href"),
    ]
