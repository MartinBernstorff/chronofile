DIR=$(dirname "$0")
cd $DIR
echo $PWD
rm -rf credentials/token.pickle
source .venv/bin/activate
python src/update_google_token.py
git add .
git commit -m "Update RescueTime Calendar API Key"
git push