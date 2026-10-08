from pathlib import Path

from pypdf import PdfReader
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parents[2]

UPLOAD_FOLDER = BASE_DIR / "uploads" / "resumes"

ALLOWED_EXTENSIONS = {"pdf"}


def is_allowed_file(filename: str) -> bool:
    """
    Check whether the uploaded file has
    an allowed extension.
    """

    if not filename:
        return False

    extension = Path(filename).suffix.lower().lstrip(".")

    return extension in ALLOWED_EXTENSIONS


def extract_pdf_text(file_path: str) -> str:
    """
    Extract text from all pages of a PDF file.
    """

    reader = PdfReader(file_path)

    text_parts = []

    for page in reader.pages:

        try:
            page_text = page.extract_text()

            if page_text:
                text_parts.append(page_text.strip())

        except Exception:
            continue

    extracted_text = "\n\n".join(text_parts).strip()

    return extracted_text


def save_resume_file(file, user_id: int):
    """
    Save uploaded resume PDF to the user's
    resume upload directory.

    Returns:
        tuple[str, str]
        (saved_file_path, original_file_name)
    """

    original_filename = secure_filename(
        file.filename or ""
    )

    if not original_filename:
        raise ValueError(
            "A valid file name is required."
        )

    if not is_allowed_file(original_filename):
        raise ValueError(
            "Only PDF resume files are allowed."
        )

    user_folder = (
        UPLOAD_FOLDER / str(user_id)
    )

    user_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    existing_files = list(
        user_folder.glob("resume_*.pdf")
    )

    next_number = len(existing_files) + 1

    saved_filename = (
        f"resume_{next_number}.pdf"
    )

    saved_path = user_folder / saved_filename

    file.save(saved_path)

    return (
        str(saved_path),
        original_filename
    )