Vendor Integration for PKCE Workflow
====================================

This is a derived version from David's example for QA: https://bbgithub.dev.bloomberg.com/draifaizen/third-party-app

Desktop Setup
====================================

### Python Dependencies
- `python -m pip install --index-url=https://bcms.bloomberg.com/pip/simple blpapi`
- `python -m pip install aiohttp`

### Run the App
1. Go to front-end and run python -m http.server 8080
2. Go to server and run python main-non-simplified.py or python main-simplified.py


Mobile Setup
====================================

### Software Requirements
1. Android Studio - [Click to Download](https://developer.android.com/studio/?gclid=CjwKCAjwzaSLBhBJEiwAJSRokpgT-K1UQBkbDh63lunacRe1tIn0eVSGDytE_y0sAzjl2J1Uj1zoNhoCPn0QAvD_BwE&gclsrc=aw.ds)

### Python Dependencies
- `python -m pip install --index-url=https://bcms.bloomberg.com/pip/simple blpapi`
- `python -m pip install aiohttp`

### Setup on Android Simulator
1. Create a virtual device from ADV Manager. Make sure choose the Android version with the Google Play
2. Start the virtual device
3. Go to Google Play and install two apps: Bloomberg Professional - [App](https://play.google.com/store/apps/details?id=com.bloomberg.android.anywhere&hl=en_US&gl=US), Simple HTTP Server (by Phlox Development) - [App](https://play.google.com/store/apps/details?id=com.phlox.simpleserver&hl=en_US&gl=US) (Please search the keywords in Google Play on the Virtual Device)
4. Open Simple HTTP Server, click on Root Folder, go to the folder "Download" and create a new folder "mobile-front-end"
5. Upload all files under "mobile-front-end" from the repository to the new folder created on the virtual Android device. We could use Google Drive (i.e. upload to Google Drive) then go to the virtual Android, download from the Google Drive. The files downloaded will be under the folder "Download", then we can move all files into the folder "mobile-front-end" on the virtual Android.
6. Back to the Simple HTTP Server. Set the Port to be 8080
7. Start the HTTP Server.
8. Try "localhost:8080" in Chrome on the virtual Android. It should show the login page.
9. Make sure we can login the Bloomberg Professional app.

### Run the back end
1. Go to server and run python main-non-simplified.py or python main-simplified.py

### Run the app on the virtual Android
1. Open "localhost:8080" in Chrome
2. Click on the login button
3. We should see Bloomberg Professional app opened then BAPP launches the redirect URL with the token. Finally we should see the streaming page.
