#!/bin/bash

echo install python dependencies, create directories etc
# TODO maybe separate runtime scripts and setup/maintenance scripts ?

[[ ! -f .env ]] && echo ERROR: .env is missing && exit 99

date
chmod 700 .env 

python3 -m venv venv
source venv/bin/activate
set -v
pip install --upgrade pip
python3 -m pip install -r requirements.txt

[[ ! -e output ]] && mkdir data_csv data_zip output

TODAY=$(date +"%Y-%m-%d")
NOW=$(date +"%Y-%m-%d %H:%M")
LOGFILE=hornet.log
echo >>$LOGFILE $(date +"%Y-%m-%d %H:%M") start download  
python3 src/download.py
date 

# use fake data to simulate an output for our demo-website 
cp "data_csv/Vespa velutina.csv"    output/oberservations.csv
cp "data_csv/Vespa velutina.csv"    output/question-1-2024.csv
cp "data_csv/Vespa velutina.csv"    output/question-1-2025.csv
cp "data_csv/Vespa velutina.csv"    output/question-2-2025.csv
echo >>$LOGFILE $(date +"%Y-%m-%d %H:%M") done  
echo $(date +"%Y-%m-%d %H:%M") >last_run.txt
