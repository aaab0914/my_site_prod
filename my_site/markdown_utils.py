"""Shared Markdown rendering with HTML sanitization to prevent stored XSS."""
import bleach
import markdown

ALLOWED_TAGS = [
    "p", "br", "hr",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "strong", "em", "b", "i", "u", "s", "del", "sup", "sub",
    "a", "img",
    "ul", "ol", "li",
    "blockquote", "pre", "code",
    "table", "thead", "tbody", "tr", "th", "td",
    "div", "span",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title"],
    "img": ["src", "alt", "title"],
    "code": ["class"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def render_markdown(text):
    html = markdown.markdown(text or "")
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
