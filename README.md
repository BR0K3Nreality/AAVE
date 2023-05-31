# AAVE

![alt text](./2.png)

Generate audio that represents the creative emotions that are being conveyed in provided image. The program also takes in an audio file an generates a visual representation of the audio to mimick as close as artistically intended by audio.  The overall concept is the relation of music and emotion.

## To use the app:

1. Navigate to the server folder from the terminal.
2. To install dependencies run: pip install -r < requirements.txt
3. Next run, python3 server.py
4. That should start the server on port 1223, if you want to use a different port you can specify like this:
  python3 server.py <port>, ex. python3 server.py 1234
  
5. Lastly navigate from your browser to: http://localhost:1223/apidocs or  http://localhost:[port_you_specified]/apidocs, this will take you to swagger where you cna test the convert file endpoint, by click on the convert method and then 'try it yourself' button.

6. Upload an image and click execute. A download button will apear, once file downloaded.
7. I recommend using the site: https://signal.vercel.app to play around with the .mid file. You can upload the file here by clicking on ' File' then 'Upload file'
  
Hope you Enjoy 😃
