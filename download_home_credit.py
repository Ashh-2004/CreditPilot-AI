
import kagglehub
import shutil
from pathlib import Path

print("Downloading Home Credit Default Risk dataset...")

# Download dataset from Kaggle
download_path = kagglehub.dataset_download("anggundwilestari/home-credit")


source = Path(download_path)
destination = Path("data/home_credit")

destination.mkdir(parents=True, exist_ok=True)

# Find and copy all CSV files
csv_files = list(source.rglob("*.csv"))

if not csv_files:
    raise RuntimeError("No CSV files found in downloaded dataset.")

for file in csv_files:
    target = destination / file.name
    shutil.copy2(file, target)
    print(f"Copied: {file.name}")

print("\nDownload completed!")
print("Dataset location:", destination.resolve())
print("Total CSV files:", len(csv_files))
