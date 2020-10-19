# insert_image_to_smath

This is a small utility for use with the Mono/Linux version of SMath. It allows the user to grab an image from a selected area of the screen, and insert the image into one or more SMath files.

Requires Python 3, PyQt 5, python3-xlib, and Linux with X Windows

[![Application screenshot](/images/Screenshot.png "Application screenshot")]

Instructions:
 - Close all ".sm" files that will have an image inserted, or exit SMath
 - Start the screen capture utility (e.g. set it as executable or run "python3 insert_image_to_smath.py" from the command line or shortcut)
 - Make sure the screen area you want to capture is visible (not minimized or hidden behind any window except this utility)
 - Click the "Select Area" button. The utility will hide itself.
 - Click and drag a rectangular selection box around the screen area you want to capture.
 - Once the left mouse button is released the utility will reappear, with a preview of the captured image in the field above the "Select Area" button.
 - Click the "Select File(s)" button, and choose the desired files from the resulting dialog.
 - Confirm the selected files in the list, then click the "Insert Image Into File(s)" button.
 - When the file is re-opened from SMath, the image will be in the top left corner of the first page, just drag it where it needs to go.

 **Warning**
 This tool writes directly to your SMath (.sm) files. It is **strongly** advised to make backups prior to using.

Much of the code in this utility was borrowed from:
 - https://gist.github.com/aspotton/1888298869c8adf59a577f2fe9d32fc8
 - https://gist.github.com/initbrain/6628609
