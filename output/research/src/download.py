# taken from C:\data\vsstudiocode-repo\nabu-asian-hornet-project-research\notebooks\pygbif_batch_download_notebook.ipynb

import os
from dotenv import load_dotenv, dotenv_values 

import time
import zipfile
import io
import pandas as pd
from pygbif import occurrences, species

load_dotenv()
GBIF_user  = os.getenv("GBIF_user")
GBIF_pwd   = os.getenv("GBIF_pwd")
GBIF_email = os.getenv("GBIF_email")

data_folder = "data_csv"
data_zip_folder = "data_zip"


name_tmp = 'Vespa velutina'
# 'Vespa crabro'


TAXA = {
    # Honigbienen
    "Apis mellifera":       species.name_backbone(scientificName="Apis mellifera"),
    # Hummeln (Gattung)
    "Bombus":               species.name_backbone(scientificName="Bombus"),
    # Gemeine Wespe & Deutsche Wespe (Gattung Vespula)
    "Vespula":              species.name_backbone(scientificName="Vespula"),
    # Langkopfwespen (Dolichovespula – Hornissen-ähnliche)
    "Dolichovespula":       species.name_backbone(scientificName="Dolichovespula"),
    # Echte Hornisse
    "Vespa crabro":         species.name_backbone(scientificName="Vespa crabro"),
    # Asiatische Hornisse (invasiv)
    "Vespa velutina":       species.name_backbone(scientificName="Vespa velutina"),
}

taxa_keys_dict = {}
for name, key in TAXA.items():
    taxa_keys_dict[name] = key['usage']['key']

key_tmp = taxa_keys_dict[name_tmp]

# 1. Download 
res = occurrences.download(
    [f"taxonKey = {key_tmp}", "country = DE"],
    user  = GBIF_user,
    pwd   = GBIF_pwd,
    email = GBIF_email
)

download_key = res[0]  # z.B. "0001234-231120084113126"

# 2. Wait for GBIF
print("Wait for GBIF...")
while True:
    meta = occurrences.download_meta(download_key)
    status = meta["status"]
    print(f"  Status: {status}", end="\r")
    if status == "SUCCEEDED":
        print("Meta Data done!")
        break
    elif status == "FAILED":
        raise RuntimeError("GBIF Download failed")
    time.sleep(30)  # alle 30 Sekunden prüfen

# 3. ZIP download
occurrences.download_get(download_key, path=f"{data_zip_folder}") # → saves e.g. "0001234-231120084113126.zip"


# 4. ZIP to DataFrme
zip_path = f"{data_zip_folder}/{download_key}.zip"

with zipfile.ZipFile(zip_path) as z:
    name = [n for n in z.namelist()][0] 
    print(f"Reading: {name}")
    with z.open(name) as f:
        df = pd.read_csv(f, sep="\t", low_memory=False)

print(f"\nDataframe loaded: {len(df):,} Rows, {len(df.columns)} Columns")


df.to_csv(f"{data_folder}/{name_tmp}.csv", index=False)

