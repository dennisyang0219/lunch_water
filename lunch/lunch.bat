@ECHO 

cmd /k "cd /d %cd% &  d:\venv_lunch\Scripts\activate & cd /d %cd% &  streamlit run LunchApp.py --server.port 5678 --server.maxUploadSize=1"
PAUSE
