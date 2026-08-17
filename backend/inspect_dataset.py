import openpyxl
import pandas as pd

def inspect():
    file_path = "uploaded_active_dataset.xlsx"
    wb = openpyxl.load_workbook(file_path, read_only=True)
    print("Sheet Names:", wb.sheetnames)
    
    df = pd.read_excel(file_path, nrows=10)
    print("\nColumns:")
    for col in df.columns:
        print(f" - {col}")
        
    print("\nSample Data (first 2 rows):")
    print(df.head(2).to_dict(orient="records"))

if __name__ == "__main__":
    inspect()
