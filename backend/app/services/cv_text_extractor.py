from pathlib import Path

from docx import Document
from pypdf import PdfReader


class CVTextExtractionError(ValueError):
    """Raised when a supported CV cannot be read safely."""


def extract_cv_text(path: Path) -> str:
    """Extract normalized text from a PDF or DOCX document."""
    suffix = path.suffix.lower()
    try:
        if suffix == ".pdf":
            reader = PdfReader(str(path))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        elif suffix == ".docx":
            document = Document(str(path))
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        else:
            raise CVTextExtractionError("Unsupported CV file type")
    except Exception as exc:
        if isinstance(exc, CVTextExtractionError):
            raise
        raise CVTextExtractionError("Unable to extract text from CV") from exc

    normalized = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if not normalized:
        raise CVTextExtractionError("CV contains no extractable text")
    return normalized
