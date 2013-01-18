import os
import gtk
import subprocess
import time

if os.name == 'nt' :
    import wexpect
    expect = wexpect
elif os.name == 'posix' :
    import pexpect
    expect = pexpect
else :
    raise ImportError("Sorry: no implementation for your platform ('%s') available" % (os.name,))

from threading import Thread
import datetime

class ProcessLog(Thread):
    def __init__(self, msp430_instance, command):
        Thread.__init__(self)
        self.msp430 = msp430_instance
        self.command = command
        
    def run(self):
        print "thread processlog starts.."   
        child = expect.spawn(self.command)
   
        while True:
            try:       
                child.expect('\r')
                gtk.threads_enter()
                self.msp430.TextBufferOfMsp.insert_at_cursor(child.before)
                gtk.threads_leave()
            except:
                break
                                
            time.sleep(0.1)
            
        print "thread processlog stopped.."
        
class Msp430():   

    def on_ButtonOfMspConnectByApi_clicked(self, widget, data=None):
        print "todo"
                                
    def show_current_time(self):
        self.TextBufferOfMsp.insert_at_cursor(str(datetime.datetime.now()) + '\n')
        
    def on_ButtonOfMspEraseByApi_clicked(self,widget, data=None):
        command = 'python msp430-jtag.pyc --time -p /dev/ttyACM0 -e'
        ProcessLog(self, command).start() 

    def on_ButtonOfMspErase_clicked(self, widget, data=None):
        self.proc = subprocess.Popen(['python', 'msp430-jtag.pyc', '--time', '-p', self.device, '-e'], 
                                shell=False, 
                                stderr=subprocess.PIPE)
        self.TextBufferOfMsp.insert_at_cursor(self.proc.communicate()[1])

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

    def __init__(self):
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
        self.FrameOfMspApi = builder.get_object("FrameOfMspApi")  
        
        self.FileFilterForView = builder.get_object("filefilter1")
        self.FileFilterForView.add_pattern("*.hex")
        self.FileFilterForView.add_pattern("*.ihex")
        self.FileChooserButtonOfHex = builder.get_object("FileChooserButtonOfHex")
        self.FileChooserButtonOfApiHex = builder.get_object("FileChooserButtonOfApiHex")
        
        default_hex_file = './lavida.hex'
        if os.path.isfile(default_hex_file):
            self.FileChooserButtonOfHex.set_filename(default_hex_file)
            self.FileChooserButtonOfApiHex.set_filename(default_hex_file)
                    
        
    def main(self):
        self.FrameOfMspApi.set_visible(True)
        self.window.show_all()    
        
        gtk.threads_init()
        gtk.threads_enter()
        gtk.main()
        gtk.threads_leave()      
  
if __name__ == "__main__":
    msp = Msp430()
    msp.main()
                