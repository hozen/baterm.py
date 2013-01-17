import os
import gtk
import subprocess

class Msp430():   
    def on_ButtonOfMspErase_clicked(self, widget, data=None):
        proc = subprocess.Popen(['python', 'msp430-jtag.pyc', '--time', '-p', self.device, '-e'], 
                                shell=False, 
                                stderr=subprocess.PIPE)
        self.TextBufferOfMsp.insert_at_cursor(proc.communicate()[1])

    def on_ButtonOfEraseCheck_clicked(self, widget, data=None):
        proc = subprocess.Popen(['python', 'msp430-jtag.pyc', '--time', '-p', self.device, '-E'], 
                                shell=False, 
                                stderr=subprocess.PIPE)
        self.TextBufferOfMsp.insert_at_cursor(proc.communicate()[1])

    def on_ButtonOfMspProgram_clicked(self, widget, data=None):
        file = self.FileChooserButtonOfHex.get_filename()
        if file != None:
            filename, fileext = os.path.splitext(file)
            if fileext == ".hex" or fileext == ".ihex":
                proc = subprocess.Popen(['python', 'msp430-jtag.pyc', '--time', '-p', self.device, '-P', '-i', 'ihex', file], 
                                shell=False, 
                                stderr=subprocess.PIPE)
                self.TextBufferOfMsp.insert_at_cursor(proc.communicate()[1])
        
    def on_ButtonOfMspReset_clicked(self, widget, data=None):
        proc = subprocess.Popen(['python', 'msp430-jtag.pyc', '-p', self.device, '-r'], 
                                shell=False, 
                                stderr=subprocess.PIPE)
        self.TextBufferOfMsp.insert_at_cursor(proc.communicate()[1])
                        
    def on_ButtonOfMspProgramAll_clicked(self, widget, data=None):
        file = self.FileChooserButtonOfHex.get_filename()
        if file != None:
            filename, fileext = os.path.splitext(file)
            if fileext == ".hex" or fileext == ".ihex":
                proc = subprocess.Popen(['python', 'msp430-jtag.pyc', '--time', '-p', self.device, '-eE', '-PV', '-r', '-i', 'ihex', self.FileChooserButtonOfHex.get_filename()], 
                                        shell=False, 
                                        stderr=subprocess.PIPE)
                self.TextBufferOfMsp.insert_at_cursor(proc.communicate()[1])        
        
    def on_TextViewOfMsp_size_allocate(self, widget, data=None):
        adj = self.ScrolledWindowOfMsp.get_vadjustment()
        adj.set_value(adj.upper - adj.page_size)        
                
    def run(self, parent_window):
        self.window.set_transient_for(parent_window)   # will make the child window located at center of main window. why??
        self.window.show_all()

    def __init__(self, portlist):
        if os.name == 'posix' :
            self.device = '/dev/ttyACM0'
            os.environ['LIBMSPGCC_PATH'] = '/usr/lib'
        else:
            self.device = 'TIUSB'
        builder = gtk.Builder()
        builder.add_from_file("msp430.glade")
        builder.connect_signals(self)
        self.window = builder.get_object("WindowOfMsp430")
        self.TextBufferOfMsp= builder.get_object("textbuffer1")
        self.ScrolledWindowOfMsp = builder.get_object("ScrolledWindowOfMsp")
        
        self.FileFilterForView = builder.get_object("filefilter1")
        self.FileFilterForView.add_pattern("*.hex")
        self.FileFilterForView.add_pattern("*.ihex")
        self.FileChooserButtonOfHex = builder.get_object("FileChooserButtonOfHex")
        default_hex_file = './lavida.hex'
        if os.path.isfile(default_hex_file):
            self.FileChooserButtonOfHex.set_filename(default_hex_file)