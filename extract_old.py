import warnings
import sys
# Suppress NumPy MINGW-W64 experimental warning on Windows
# This warning appears when NumPy is built with MINGW-W64 (experimental on Windows)
warnings.filterwarnings("ignore", message=".*Numpy built with MINGW-W64.*")
warnings.filterwarnings("ignore", message=".*MINGW-W64.*")

from helpers.extract_word import extract_info_from_word
from helpers.extract_pdf import extract_info_from_pdf
from pathlib import Path
from tqdm import tqdm
import pandas as pd


def _numeric_or_text_key(stem: str):
    try:
        return (0, int(stem))
    except ValueError:
        return (1, stem)


def _build_ordered_sequence_by_stem(folder: Path):
    """Return files ordered as stem.docx then stem.pdf by ascending stem.

    Groups files by base FILENAME (stem). Within each group, orders .docx before .pdf.
    Across groups, sorts stems numerically when possible, otherwise lexicographically.
    """
    mapping = {}
    for p in folder.rglob("*.docx"):
        if not p.is_file():
            continue
        mapping.setdefault(p.stem, {})["docx"] = p
    for p in folder.rglob("*.pdf"):
        if not p.is_file():
            continue
        mapping.setdefault(p.stem, {})["pdf"] = p

    ordered_files = []
    for stem in sorted(mapping.keys(), key=_numeric_or_text_key):
        for ext in ("docx", "pdf"):
            path_obj = mapping[stem].get(ext)
            if path_obj is not None:
                ordered_files.append(path_obj)
    return ordered_files


if __name__ == "__main__":
    print("Document Extractor (Word + PDF)")
    print("=" * 50)

    base_dir = Path(__file__).parent
    men_dir = base_dir / "men"
    women_dir = base_dir / "women"

    rows = []

    # Process men first, interleaving docx/pdf by base FILENAME
    if men_dir.exists():
        men_files = _build_ordered_sequence_by_stem(men_dir)
        for f in tqdm(men_files, desc="Processing men", unit="file"):
            if f.suffix.lower() == ".pdf":
                injury_data = extract_info_from_pdf(str(f))
            else:
                injury_data = extract_info_from_word(str(f))
            if injury_data is None:
                continue
            # store path relative to men/ to drop the 'men/' prefix
            injury_data["FILENAME"] = str(f.relative_to(men_dir)) if f.is_relative_to(men_dir) else str(f)
            injury_data["SEX"] = "Male"
            rows.append(injury_data)

    # Then process women, interleaving docx/pdf by base FILENAME
    if women_dir.exists():
        women_files = _build_ordered_sequence_by_stem(women_dir)
        for f in tqdm(women_files, desc="Processing women", unit="file"):
            if f.suffix.lower() == ".pdf":
                injury_data = extract_info_from_pdf(str(f))
            else:
                injury_data = extract_info_from_word(str(f))
            if injury_data is None:
                continue
            # store path relative to women/ to drop the 'women/' prefix
            injury_data["FILENAME"] = str(f.relative_to(women_dir)) if f.is_relative_to(women_dir) else str(f)
            
            injury_data["SEX"] = "Female"
            rows.append(injury_data)

    if not rows:
        print("No .docx or .pdf files found under 'men' or 'women'.")
    else:
        df = pd.DataFrame(rows)
        # Ensure FILENAME is the first column
        ordered_cols = ["FILENAME", "SEX"] + [c for c in df.columns if c not in ("FILENAME", "SEX")]
        df = df[ordered_cols]
        output_excel = base_dir / "injury_data.xlsx"
        df.to_excel(output_excel, index=False)
        print(f"Saved Excel to {output_excel}")