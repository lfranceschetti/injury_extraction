from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import pandas as pd
from extract_word_new import extract_info_from_word
from extract_pdf_new import extract_info_from_pdf

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
    directory = base_dir / "updated"

    rows = []

    # Process men first, interleaving docx/pdf by base FILENAME
    if directory.exists():
        files = _build_ordered_sequence_by_stem(directory)
        for f in tqdm(files, desc="Processing files", unit="file"):
            if f.suffix.lower() == ".pdf":
                injury_data = extract_info_from_pdf(str(f))
            else:
                injury_data = extract_info_from_word(str(f))
            if injury_data is None:
                continue
            # store path relative to directory to drop the 'directory/' prefix
            file_name = str(f.relative_to(directory)) if f.is_relative_to(directory) else str(f)
            injury_data["FILENAME"] = file_name

            injury_data["TEAM"] = file_name.split(",")[0] if len(file_name.split(",")) > 1 else "UNKNOWN"


            injury_data["UPDATED_AT"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rows.append(injury_data)

    if not rows:
        print("No .docx or .pdf files found under 'updated'.")
    else:
        df = pd.DataFrame(rows)
        # Ensure FILENAME is the first column
        ordered_cols = ["FILENAME"] + [c for c in df.columns if c != "FILENAME"]
        df = df[ordered_cols]
        #Print the column names 
        output_excel = base_dir / "injury_data_updated.xlsx"
        df.to_excel(output_excel, index=False)
        print(f"Saved Excel to {output_excel}")