# RASA Challenge

# To create conda environment
1. conda create -n rasa3.5 python=3.10.10
2. conda activate rasa3.5
3. pip install rasa==3.5.4
4. pip install pandas==2.0.1

# To train Rasa
Inside each rasa directory (en and es) run: "rasa train"

# Rasa Run with local files
Inside each rasa directory

**ES**

rasa run --model model --credentials ./credentials.yml --endpoints ./endpoints.yml --debug --cors "*" --enable-api --port 5005

# Rasa Actions
Run "pip install -r req_actions.txt" before running the actions server


To start rasa actions run: Inside each rasa directory 

**ES**

rasa run actions --port 5055

# To start rasa shell in cmd:

rasa shell --model model --credentials ./credentials.yml --endpoints ./endpoints.yml --debug --cors "*" --enable-api