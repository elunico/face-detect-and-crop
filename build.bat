
:: in order to build, you must setup a virtual env at ./venv in the root of the project
:: then activate it and run pip install -r requirements.txt
:: then run pip install pyinstaller.
:: then you can run the build.bat script and build the application

pyinstaller --add-data "model/haarcascade_frontalface_default.xml;." --paths ./venv/Lib/site-packages --windowed -F facedetect.py

pyinstaller --paths ./venv/Lib/site-packages --windowed -F shrink.py
