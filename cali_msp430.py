import os
import gtk
import subprocess
import time

if os.name == 'posix' :
    import pexpect

from threading import Thread

class ProcessLog(Thread):        

    def __init__(self, msp430_instance, cmds):
        Thread.__init__(self)
        self.msp430 = msp430_instance
        jtagfile = './msp430-jtag.py'
        if not os.path.isfile(jtagfile):
            jtagfile = './msp430-jtag.pyc'
        self.cmds = ['python', jtagfile, '--time', '-p']
        if os.name == 'posix':
            self.cmds.append('/dev/ttyACM0')
        else:
            self.cmds.append('TIUSB')
            
        self.cmds += cmds
        
    def run(self):
        print "thread processlog starts.."   
        if os.name == 'posix':
            command = ''
            for cmd in self.cmds:
                command += cmd
                command += ' '
            start_time = time.time()
            child = pexpect.spawn(command)
       
            while True:
                try:       
                    child.expect('\r')
                    gtk.threads_enter()
                    self.msp430.TextBufferOfMsp.insert_at_cursor(child.before)
                    gtk.threads_leave()
                except:
                    gtk.threads_enter()
                    print child.after
                    self.msp430.TextBufferOfMsp.insert_at_cursor("\nTime: " + str(time.time() - start_time) + 's\n')
                    gtk.threads_leave()
                    break
                                    
                time.sleep(0.1)
        else:
            proc = subprocess.Popen(self.cmds, 
                                    shell=False, 
                                    stderr=subprocess.PIPE)
            gtk.threads_enter()
            self.msp430.TextBufferOfMsp.insert_at_cursor(proc.communicate()[1])
            gtk.threads_leave()

            
        print "thread processlog stopped.."
        
class Msp430():   
    def on_WindowOfMsp430_destroy(self, widget, data=None):
        if self.not_from_parent_gtk == 1:
            print "msp gtk quit.."
            gtk.main_quit()

    def on_ButtonOfMspConnectByApi_clicked(self, widget, data=None):
        print "todo"
                                        
    def on_ButtonOfMspEraseByApi_clicked(self,widget, data=None):
        cmds = ['-e']
        ProcessLog(self, cmds).start() 

    def on_ButtonOfMspErase_clicked(self, widget, data=None):
        cmds = ['-e']
        ProcessLog(self, cmds).start() 

    def on_ButtonOfEraseCheck_clicked(self, widget, data=None):
        cmds = ['-E']
        ProcessLog(self, cmds).start() 

    def on_ButtonOfMspProgram_clicked(self, widget, data=None):
        file = self.FileChooserButtonOfHex.get_filename()
        if file != None:
            filename, fileext = os.path.splitext(file)
            if fileext == ".hex" or fileext == ".ihex":
                cmds = ['-P', '-i', 'ihex', file]
                ProcessLog(self, cmds).start() 
                
    def on_ButtonOfMspReset_clicked(self, widget, data=None):
        cmds = ['-r'], 
        ProcessLog(self, cmds).start() 
                        
    def on_ButtonOfMspProgramAll_clicked(self, widget, data=None):
        file = self.FileChooserButtonOfHex.get_filename()
        if file != None:
            filename, fileext = os.path.splitext(file)
            if fileext == ".hex" or fileext == ".ihex":
                cmds = ['-eE', '-PV', '-r', '-i', 'ihex', self.FileChooserButtonOfHex.get_filename()]
                ProcessLog(self, cmds).start() 
                
    def on_TextViewOfMsp_size_allocate(self, widget, data=None):
        adj = self.ScrolledWindowOfMsp.get_vadjustment()
        adj.set_value(adj.upper - adj.page_size)        
                
    def run(self, parent_window):
        self.window.set_transient_for(parent_window)   # will make the child window located at center of main window. why??
        self.window.show_all()

    def __init__(self):
        if os.name == 'posix' :
            os.environ['LIBMSPGCC_PATH'] = '/usr/lib'
        builder = gtk.Builder()
        builder.add_from_file("./glades/msp430.glade")
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
        
        default_hex_file = './ihexfiles/lavida.hex'
        if os.path.isfile(default_hex_file):
            self.FileChooserButtonOfHex.set_filename(default_hex_file)
            self.FileChooserButtonOfApiHex.set_filename(default_hex_file)
                    
        self.not_from_parent_gtk = 0    # was activated by cali_test main window
        
    def main(self):
        self.FrameOfMspApi.set_visible(True)
        self.window.show_all()    
        
        self.not_from_parent_gtk = 1
        gtk.threads_init()
        gtk.threads_enter()
        gtk.main()
        gtk.threads_leave()      
  
if __name__ == "__main__":
    msp = Msp430()
    msp.main()
                