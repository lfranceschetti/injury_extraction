from extract import extract_xml_from_docx, extract_injury_form_data, print_injury_data
import pandas as pd

if __name__ == "__main__":

    
    # Usage examples
    print("Word Document XML Extractor")
    print("=" * 50)

    files = [
        # "1.docx",
        # "2.docx",
        # "3.docx",
        "xxxx_yy.docx",
    ]

    # Collect results
    rows = []
    for f in files:
        print(f"Extracted data for {f}:")
        injury_data = extract_injury_form_data(f)
        injury_data["filename"] = f
        rows.append(injury_data)
        for k, v in injury_data.items():
            print(f"{k}: {v}")
        print("-" * 50)

    # Write to Excel with keys as columns
    if rows:
        df = pd.DataFrame(rows)
        # Ensure filename is the first column
        cols = ["filename"] + [c for c in df.columns if c != "filename"]
        df = df[cols]
        output_excel = "injury_data.xlsx"
        df.to_excel(output_excel, index=False)
        print(f"Saved Excel to {output_excel}")