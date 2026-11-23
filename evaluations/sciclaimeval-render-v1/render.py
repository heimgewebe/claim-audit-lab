"""Deterministic row-level display of small source tables with original-span proofs.

Presentation is derived data. Source bytes remain canonical; neither this module
nor a model-produced quote authenticates the original scientific publication.
"""
from __future__ import annotations

import hashlib
from html import unescape
import re

RENDERER_ID = "sciclaimeval-native-row-display-v1"
_LATEX_INLINE = re.compile(r"\\(?:textbf|textit|emph|underline|mathrm|mathbf)\{([^{}]*)\}")
_LATEX_RULE = re.compile(r"\\(?:midrule|bottomrule|toprule|hline|cmidrule)(?:\{[^{}]*\})?")
_HTML_ROW = re.compile(r"<tr\b[^>]*>(.*?)</tr\s*>", re.I | re.S)
_HTML_CELL = re.compile(r"<t[dh]\b[^>]*>(.*?)</t[dh]\s*>", re.I | re.S)
_HTML_TAG = re.compile(r"<[^>]*>")
# Reject rather than glue distinct values or lose scientific notation inside a cell.
_UNSUPPORTED_HTML_CELL_MARKUP = re.compile(
    r"<(?:br|p|div|li|hr|sup|sub|math|img|ul|ol|table)\b", re.I,
)
_LATEX_TABLE_START = re.compile(r"\\begin\{tabular\*?\}|\\begin\{tabularx\}")
_LATEX_TABLE_END = re.compile(r"\\end\{tabular\*?\}|\\end\{tabularx\}")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _has_unescaped_tex_comment(line: str) -> bool:
    """An odd number of preceding backslashes means '%' is escaped."""
    for index, character in enumerate(line):
        if character != "%":
            continue
        count = 0
        pos = index - 1
        while pos >= 0 and line[pos] == "\\":
            count += 1
            pos -= 1
        if count % 2 == 0:
            return True
    return False


def display_latex_row(raw_line: str) -> str:
    """Reduce formatting, not values; deterministic for an original source line."""
    line = raw_line.strip()
    # Remove only presentation commands around the row, not scientific values.
    for _ in range(5):
        line, hits = _LATEX_INLINE.subn(r"\1", line)
        if not hits:
            break
    line = _LATEX_RULE.sub("", line)
    line = re.sub(r"\\\\\s*(?:\\(?:midrule|hline))?\s*$", "", line)
    line = line.replace(r"\%", "%").replace(r"\_", "_")
    line = line.replace(r"\uparrow", "↑").replace(r"\downarrow", "↓")
    line = line.replace(r"\pm", "±").replace("$", "")
    line = re.sub(r"\s*&\s*", " | ", line)
    return re.sub(r"\s+", " ", line).strip(" |")


def display_html_row(source_fragment: str) -> str:
    match = _HTML_ROW.fullmatch(source_fragment)
    if not match:
        raise ValueError("Not one complete HTML table row")
    cells = []
    for cell in _HTML_CELL.finditer(match.group(1)):
        # A structural tag may separate values (1<br>2) or carry scientific
        # meaning (10<sup>3</sup>); removing it could invent a number.
        if _UNSUPPORTED_HTML_CELL_MARKUP.search(cell.group(1)):
            raise ValueError("Unsupported semantic markup inside HTML table cell")
        # HTML character entities and formatting markup are rendered, never
        # treated as literal quotations from the underlying raw HTML.
        text = unescape(_HTML_TAG.sub("", cell.group(1)))
        cells.append(re.sub(r"\s+", " ", text).strip())
    return " | ".join(cells).strip(" |")


def render_table(raw: str) -> dict:
    if not isinstance(raw, str) or not 40 <= len(raw) <= 7000:
        raise ValueError("Expected a bounded, complete native source table")
    rows = []
    if "<table" in raw.lower():
        representation = "html"
        # Regex row extraction cannot distinguish commented-out table rows
        # from visible evidence. Reject this unsupported source class rather
        # than authenticating hidden numbers or changing original offsets.
        if "<!--" in raw or "-->" in raw:
            raise ValueError("HTML comments unsupported for source-backed table evidence")
        for match in _HTML_ROW.finditer(raw):
            fragment = match.group()
            text = display_html_row(fragment)
            if text:
                rows.append((match.start(), match.end(), fragment, text))
    elif _LATEX_TABLE_START.search(raw):
        representation = "latex"
        inside = False
        offset = 0
        fragment_start = 0
        buffer = []
        for line in raw.splitlines(keepends=True):
            trimmed = line.lstrip()
            if trimmed.startswith(r"\begin{tabular"):
                if inside:
                    raise ValueError("Nested tabular not supported: refuse partial rendering")
                inside = True
                buffer = []
                offset += len(line)
                continue
            if inside and trimmed.startswith(r"\end{tabular"):
                # TeX permits the final data row without a trailing \\\\.
                # Bind the entire final row to its original contiguous span.
                if any("&" in part for part in buffer):
                    fragment = raw[fragment_start:offset]
                    text = display_latex_row(fragment)
                    if text:
                        rows.append((fragment_start, offset, fragment, text))
                inside = False
                buffer = []
                offset += len(line)
                continue
            if inside:
                if trimmed.startswith("%"):
                    # A full TeX comment line is not scientific table data.
                    # Never include it in a pending multiline source row.
                    if buffer:
                        raise ValueError("TeX comment inside unfinished table row")
                    offset += len(line)
                    continue
                if _has_unescaped_tex_comment(line):
                    # TeX would ignore the rest of the line, whereas our
                    # renderer would otherwise falsely authenticate it.
                    raise ValueError("Unescaped TeX data-row comment unsupported")
                # Reject multiple logical rows sharing one physical line.
                # Escaped breaks within a known tabincell macro aren't rows.
                without_tabincell = re.sub(
                    r"\\tabincell\{[^{}]*\}\{[^{}]*\}", "", line,
                )
                # An inline nested tabular within a cell can itself use
                # TeX line breaks. Mask only complete same-line inner tables;
                # never mask separate outer-row delimiters.
                without_inner = re.sub(
                    r"\\begin\{tabular\}.*?\\end\{tabular\}", "",
                    without_tabincell,
                )
                if (
                    r"\begin{tabular}" in without_inner
                    or r"\end{tabular}" in without_inner
                ):
                    raise ValueError("Incomplete inline tabular cell unsupported")
                if without_inner.count(r"\\") > 1:
                    raise ValueError(
                        "Multiple LaTeX row delimiters on one line are unsupported"
                    )
                if not buffer:
                    fragment_start = offset
                if not trimmed.startswith("%"):
                    buffer.append(line)
                # Only a physical row terminator at the END of a source line
                # closes one logical data row. Multiline cells are not discarded.
                tail = line.rstrip()
                if tail.endswith(r"\\") or any(tail.endswith(r"\\ " + "\\" + command)
                                              for command in ("midrule","bottomrule","hline","toprule")):
                    fragment = raw[fragment_start:offset + len(line.rstrip("\r\n"))]
                    if "&" in fragment:
                        text = display_latex_row(fragment)
                        if text:
                            rows.append((fragment_start, fragment_start + len(fragment), fragment, text))
                    buffer = []
            offset += len(line)
        if inside or any("&" in part for part in buffer):
            raise ValueError("Missing table closure or complete row delimiter")
    else:
        raise ValueError("Unknown native table presentation format")
    if len(rows) < 2 or len(rows) > 100:
        raise ValueError("Unusable table: no bounded row-level display")
    records = []
    for i, (start, end, fragment, text) in enumerate(rows):
        if raw[start:end] != fragment:
            raise ValueError("Source substring offset mismatch")
        records.append({
            "row": i, "display": text, "display_sha256": sha(text.encode()),
            "source_char_start": start, "source_char_end": end,
            "original_row_sha256": sha(fragment.encode()),
        })
    shown = "\n".join(row["display"] for row in records)
    if len(shown) > len(raw) * 2:
        raise ValueError("Rendered source unexpectedly enlarged")
    return {
        "renderer": RENDERER_ID, "source_sha256": sha(raw.encode()),
        "representation": representation,
        "rendered_source": shown,
        "rendered_sha256": sha(shown.encode()),
        "rows": records,
    }


def prove_quote(raw: str, view: dict, evidence_span: str) -> dict | None:
    """Prove a quote in exactly ONE rendered row with a real source span.

    For an insufficient judgment an empty quote is allowed, as in the
    existing exact-span parser. A rendered quote spanning multiple
    rows or matching multiple rows has no unique single-row provenance.
    """
    if render_table(raw) != view:
        raise ValueError("The displayed source is not identical to source-derived rows")
    if not evidence_span:
        return None
    matches = [
        row for row in view["rows"] if evidence_span in row["display"]
    ]
    if len(matches) != 1:
        raise ValueError("Rendered quote has no unique source row")
    row = matches[0]
    fragment = raw[row["source_char_start"]:row["source_char_end"]]
    if sha(fragment.encode()) != row["original_row_sha256"]:
        raise ValueError("Raw source evidence row drifted")
    expected = (
        display_latex_row(fragment) if view["representation"] == "latex"
        else display_html_row(fragment)
    )
    if expected != row["display"]:
        raise ValueError("Row did not derive deterministically from original source")
    return {
        "renderer": RENDERER_ID,
        "original_source_sha256": view["source_sha256"],
        "original_row_sha256": row["original_row_sha256"],
        "original_source_chars": [row["source_char_start"], row["source_char_end"]],
        "rendered_source_sha256": view["rendered_sha256"],
        "display_row_sha256": row["display_sha256"],
        "row_index": row["row"],
        "display_quote_start": row["display"].index(evidence_span),
        "quoted_display_sha256": sha(evidence_span.encode()),
        "display_quote_is_raw_verbatim": evidence_span in fragment,
    }