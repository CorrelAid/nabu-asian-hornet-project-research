#!/bin/bash

echo check run-status (just one successful run per day), run python script to download the data

echo tbd 

echo use C:\data\vsstudiocode-repo\nabu-asian-hornet-project-research\notebooks\pygbif_batch_download_notebook.ipynb

set -x -v

python src/download.py 

sleep 60

