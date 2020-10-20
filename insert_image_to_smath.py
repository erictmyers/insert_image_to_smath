#!/usr/bin/env python3

# Adapted from code at https://gist.github.com/aspotton/1888298869c8adf59a577f2fe9d32fc8

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

import sys
import mmap

from PyQt5 import QtCore,QtGui,QtWidgets,uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QFileDialog
from Xlib import X, display

class XSelect:
    def __init__(self, display):
        # X display
        self.d = display

        # Screen
        self.screen = self.d.screen()

        # Draw on the root window (desktop surface)
        self.window = self.screen.root

        self.cursor = X.NONE

        colormap = self.screen.default_colormap
        color = colormap.alloc_color(0, 0, 0)
        # Xor it because we'll draw with X.GXxor function
        xor_color = color.pixel ^ 0xffffff

        self.gc = self.window.create_gc(
            line_width = 1,
            line_style = X.LineSolid,
            fill_style = X.FillOpaqueStippled,
            fill_rule  = X.WindingRule,
            cap_style  = X.CapButt,
            join_style = X.JoinMiter,
            foreground = xor_color,
            background = self.screen.black_pixel,
            function = X.GXxor,
            graphics_exposures = False,
            subwindow_mode = X.IncludeInferiors,
        )

    def get_mouse_selection(self):
        started = False
        start   = dict(x=0, y=0)
        end     = dict(x=0, y=0)
        last    = None
        drawlimit = 10
        i = 0

        self.window.grab_pointer(self.d, X.PointerMotionMask|X.ButtonReleaseMask|X.ButtonPressMask,
                X.GrabModeAsync, X.GrabModeAsync, X.NONE, self.cursor, X.CurrentTime)

        self.window.grab_keyboard(self.d, X.GrabModeAsync, X.GrabModeAsync, X.CurrentTime)

        while True:
            e = self.d.next_event()

            # Window has been destroyed, quit
            if e.type == X.DestroyNotify:
                break

            # Mouse button press
            elif e.type == X.ButtonPress:
                # Left mouse button?
                if e.detail == 1:
                    start = dict(x=e.root_x, y=e.root_y)
                    started = True

                # Right mouse button?
                elif e.detail == 3:
                    return

            # Mouse button release
            elif e.type == X.ButtonRelease:
                end = dict(x=e.root_x, y=e.root_y)
                if last:
                    self.draw_rectangle(start, last)
                break

            # Mouse movement
            elif e.type == X.MotionNotify and started:
                i = i + 1
                if i % drawlimit != 0:
                    continue

                if last:
                    self.draw_rectangle(start, last)
                    last = None

                last = dict(x=e.root_x, y=e.root_y)
                self.draw_rectangle(start, last)

        self.d.ungrab_keyboard(X.CurrentTime)
        self.d.ungrab_pointer(X.CurrentTime)
        self.d.sync()

        coords = self.get_coords(start, end)
        if coords['width'] <= 1 or coords['height'] <= 1:
            return
        return [coords['start']['x'], coords['start']['y'], coords['width'], coords['height']]

    def get_coords(self, start, end):
        safe_start = dict(x=0, y=0)
        safe_end   = dict(x=0, y=0)

        if start['x'] > end['x']:
            safe_start['x'] = end['x']
            safe_end['x']   = start['x']
        else:
            safe_start['x'] = start['x']
            safe_end['x']   = end['x']

        if start['y'] > end['y']:
            safe_start['y'] = end['y']
            safe_end['y']   = start['y']
        else:
            safe_start['y'] = start['y']
            safe_end['y']   = end['y']

        return {
            'start': {
                'x': safe_start['x'],
                'y': safe_start['y'],
            },
            'end': {
                'x': safe_end['x'],
                'y': safe_end['y'],
            },
            'width' : safe_end['x'] - safe_start['x'],
            'height': safe_end['y'] - safe_start['y'],
        }

    def draw_rectangle(self, start, end):
        coords = self.get_coords(start, end)
        self.window.rectangle(self.gc,
            coords['start']['x'],
            coords['start']['y'],
            coords['end']['x'] - coords['start']['x'],
            coords['end']['y'] - coords['start']['y']
        )


class Screenshot (QtWidgets.QWidget):
    def __init__(self,parent=None):
        QtWidgets.QWidget.__init__(self,parent)
        uic.loadUi("image_capture_form.ui",self)

        self.area = None
        
        self.selectAreaButton.clicked.connect(self.selectArea)
        self.quitScreenshotButton.clicked.connect(self.close)
        self.selectFilesButton.clicked.connect(self.selectFiles)
        self.insertImageButton.clicked.connect(self.insertImage)
        
    def setInsertButtonState(self):
        readiness=0        
        if self.screenshotLabel.pixmap():
            readiness+=1
        if self.fileListWidget.count()>0:
            readiness+=1
            
        if readiness==2:
            self.insertImageButton.setEnabled(True)
        else:
            self.insertImageButton.setEnabled(False)
        
    def updateScreenshotLabel(self):
        self.screenshotLabel.setPixmap(self.originalPixmap.scaled(
                self.screenshotLabel.size(), QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation))
        
        self.setInsertButtonState()

    def selectFiles(self):        
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setNameFilter("SMath Files (*.sm)")
        dialog.setViewMode(QFileDialog.Detail)
        dialog.AcceptMode(QFileDialog.AcceptOpen)
        
        if dialog.exec_():
            self.fileListWidget.clear()
            fileNames = dialog.selectedFiles()
            
        for filename in fileNames:
            self.fileListWidget.addItem(filename)
        
        self.setInsertButtonState()

    def selectArea(self):
        self.hide()

        xs = XSelect(display.Display())
        self.area = xs.get_mouse_selection()
        self.shootScreen()
        
        self.show()

    def shootScreen(self):
        # Garbage collect any existing image first.
        self.originalPixmap = None
        screen = QApplication.primaryScreen()
        self.originalPixmap = screen.grabWindow(QApplication.desktop().winId())
        if self.area is not None:
            qi = self.originalPixmap.toImage()
            qi = qi.copy(int(self.area[0]), int(self.area[1]), int(self.area[2]), int(self.area[3]))
            self.originalPixmap = None
            self.originalPixmap = QPixmap.fromImage(qi)
            
            byte_array = QtCore.QByteArray()
            buffer = QtCore.QBuffer(byte_array)
            buffer.open(QtCore.QIODevice.WriteOnly)
            self.originalPixmap.save(buffer, 'PNG')
            self.encoded_pic=buffer.data().toBase64()
            # print(self.area[0],self.area[1],self.encoded_pic)

        self.updateScreenshotLabel()        
        self.show()
        
    def insertImage(self):
        file_list_length=self.fileListWidget.count()
        for i in range(file_list_length):
            filename=self.fileListWidget.item(i).text()
            print(filename)
            file=open(filename, 'rb+') # Open read/write binary
            s=mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_WRITE)
            print("File size before resizing is "+str(s.size()))
            # look for <regions type="content">. If found, insert line after that
            region_id=''
            content_loc=s.find(b'<regions type="content">')
            if content_loc==-1:
                # if not found, find </settings> and insert line after that with region id="0"
                index=s.find(b'</settings>')+len(b'</settings>')
                region_id='id="0" '
            else:
                index=content_loc+len(b'<regions type="content">')
                
            region_text='\n    <region '+region_id+'left="1" top="1" width="'+str(self.area[2])+'" height="'+str(self.area[3]) \
                +'" color="#000000" bgColor="#ffffff">\n      <picture>\n        <raw format="png" encoding="base64">' \
                +self.encoded_pic.data().decode()+'</raw>\n      </picture>\n    </region>'
            text_size=len(region_text)
            self.insert_bytes(file,text_size,index)            
            print("File size after resizing is "+str(s.size()))
            s.flush()
            s.close()
            file.close()
            
            file=open(filename, 'r+') # Open read/write
            file.seek(index,0)
            file.write(region_text)
            file.close()
            
        QtWidgets.QMessageBox.information(self, "Image Inserted", "Image added to "+str(file_list_length)+" files.")
            
## The functions insert_bytes, resize_file, and mmap_move are copied from https://github.com/bugatsinho/script.module.mutagen/blob/master/lib/mutagen/_util.py
    def insert_bytes(self,fobj, size, offset, BUFFER_SIZE=2 ** 16):
        """Insert size bytes of empty space starting at offset.

        fobj must be an open file object, open rb+ or
        equivalent.

        Args:
            fobj (fileobj)
            size (int): The amount of space to insert
            offset (int): The offset at which to insert the space
        Raises:
            IOError
        """

        if size < 0 or offset < 0:
            raise ValueError

        fobj.seek(0, 2)
        filesize = fobj.tell()
        movesize = filesize - offset

        if movesize < 0:
            raise ValueError

        self.resize_file(fobj, size, BUFFER_SIZE)

        self.mmap_move(fobj, offset + size, offset, movesize)

    def resize_file(self,fobj, diff, BUFFER_SIZE=2 ** 16):
        """Resize a file by `diff`.

        New space will be filled with zeros.

        Args:
            fobj (fileobj)
            diff (int): amount of size to change
        Raises:
            IOError
        """

        fobj.seek(0, 2)
        filesize = fobj.tell()

        if diff < 0:
            if filesize + diff < 0:
                raise ValueError
            # truncate flushes internally
            fobj.truncate(filesize + diff)
        elif diff > 0:
            try:
                while diff:
                    addsize = min(BUFFER_SIZE, diff)
                    fobj.write(b"\x00" * addsize)
                    diff -= addsize
                fobj.flush()
            except IOError as e:
                if e.errno == errno.ENOSPC:
                    # To reduce the chance of corrupt files in case of missing
                    # space try to revert the file expansion back. Of course
                    # in reality every in-file-write can also fail due to COW etc.
                    # Note: IOError gets also raised in flush() due to buffering
                    fobj.truncate(filesize)
                raise

    def mmap_move(self,fileobj, dest, src, count):
        """Mmaps the file object if possible and moves 'count' data
        from 'src' to 'dest'. All data has to be inside the file size
        (enlarging the file through this function isn't possible)

        Will adjust the file offset.

        Args:
            fileobj (fileobj)
            dest (int): The destination offset
            src (int): The source offset
            count (int) The amount of data to move
        Raises:
            mmap.error: In case move failed
            IOError: In case an operation on the fileobj fails
            ValueError: In case invalid parameters were given
        """

        assert mmap is not None, "no mmap support"

        if dest < 0 or src < 0 or count < 0:
            raise ValueError("Invalid parameters")

        try:
            fileno = fileobj.fileno()
        except (AttributeError, IOError):
            raise mmap.error(
                "File object does not expose/support a file descriptor")

        fileobj.seek(0, 2)
        filesize = fileobj.tell()
        length = max(dest, src) + count

        if length > filesize:
            raise ValueError("Not in file size boundary")

        offset = ((min(dest, src) // mmap.ALLOCATIONGRANULARITY) *
                mmap.ALLOCATIONGRANULARITY)
        assert dest >= offset
        assert src >= offset
        assert offset % mmap.ALLOCATIONGRANULARITY == 0

        # Windows doesn't handle empty mappings, add a fast path here instead
        if count == 0:
            return

        # fast path
        if src == dest:
            return

        fileobj.flush()
        file_map = mmap.mmap(fileno, length - offset, offset=offset)
        try:
            file_map.move(dest - offset, src - offset, count)
        finally:
            file_map.close()

if __name__=='__main__':
    if sys.version_info[0] < 3:
        print("Requires Python 3")
        sys.exit()

    a=QtWidgets.QApplication(sys.argv)
    w=Screenshot()
    w.show()
    sys.exit(a.exec_())
