from extract import extract_injury_form_data
from pathlib import Path
from tqdm import tqdm
import pandas as pd


if __name__ == "__main__":
    print("Word Document XML Extractor")
    print("=" * 50)

    base_dir = Path(__file__).parent
    men_dir = base_dir / "men"
    women_dir = base_dir / "women"

    rows = []

    # Process men first
    if men_dir.exists():
        men_files = sorted(p for p in men_dir.rglob("*.docx") if p.is_file())
        for f in tqdm(men_files, desc="Processing men", unit="file"):
            injury_data = extract_injury_form_data(str(f))
            if injury_data is None:
                continue
            # store path relative to men/ to drop the 'men/' prefix
            injury_data["filename"] = str(f.relative_to(men_dir)) if f.is_relative_to(men_dir) else str(f)
            injury_data["SEX"] = "Male"
            rows.append(injury_data)

    # Then process women
    if women_dir.exists():
        women_files = sorted(p for p in women_dir.rglob("*.docx") if p.is_file())
        for f in tqdm(women_files, desc="Processing women", unit="file"):
            injury_data = extract_injury_form_data(str(f))
            if injury_data is None:
                continue
            # store path relative to women/ to drop the 'women/' prefix
            injury_data["filename"] = str(f.relative_to(women_dir)) if f.is_relative_to(women_dir) else str(f)
            injury_data["SEX"] = "Female"
            rows.append(injury_data)

    if not rows:
        print("No .docx files found under 'men' or 'women'.")
    else:
        df = pd.DataFrame(rows)
        # Ensure filename is the first column
        ordered_cols = ["filename", "SEX"] + [c for c in df.columns if c not in ("filename", "SEX")]
        df = df[ordered_cols]
        output_excel = base_dir / "injury_data.xlsx"
        df.to_excel(output_excel, index=False)
        print(f"Saved Excel to {output_excel}")