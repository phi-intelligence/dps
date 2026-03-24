"""Minimal valid-enough PDF placeholder until real PDF generation is wired."""


def minimal_pdf_bytes(*, title: str, body_lines: list[str]) -> bytes:
    """Tiny single-page PDF (ASCII-safe) for operational placeholders."""
    safe_title = "".join(c if 32 <= ord(c) < 127 else " " for c in title)[:200]
    text = " | ".join(body_lines)[:2000]
    safe_text = "".join(c if 32 <= ord(c) < 127 else " " for c in text)
    # PDF literal string escaping
    safe_text = safe_text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    parts: list[bytes] = []
    offsets: list[int] = []

    def add(s: bytes) -> None:
        offsets.append(sum(len(x) for x in parts))
        parts.append(s)

    add(b"%PDF-1.4\n")
    # objects 1..5
    add(b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n")
    add(b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n")
    stream = (
        f"BT /F1 12 Tf 50 750 Td ({safe_title}) Tj 0 -20 Td ({safe_text[:1800]}) Tj ET".encode("ascii", errors="replace")
    )
    add(
        (
            f"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
        ).encode()
    )
    add(f"4 0 obj<</Length {len(stream)}>>stream\n".encode() + stream + b"\nendstream\nendobj\n")
    add(b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n")

    xref_pos = sum(len(x) for x in parts)
    out = b"".join(parts)
    xref = b"xref\n0 6\n0000000000 65535 f \n"
    for i in range(1, 6):
        start = offsets[i]
        xref += f"{start:010d} 00000 n \n".encode()
    trailer = (
        b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n"
        + str(xref_pos).encode()
        + b"\n%%EOF\n"
    )
    return out + xref + trailer
