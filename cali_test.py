#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk
import pango
import threading
from threading import Thread
import serial
import time
import os

import basiclex
import basparse
import basinterp

import cali_scan
import cali_msp430

if os.name == 'nt' :
    from serial.tools.list_ports_windows import *
elif os.name == 'posix' :
    from serial.tools.list_ports_posix import *
else :
    raise ImportError("Sorry: no implementation for your platform ('%s') available" % (os.name,))

class CaliTest:
    def ConvertCN(self, s):  
        return s.encode('gb18030')  

    def on_window_destroy(self, widget, data=None):
        self.serial_close_all()
        gtk.main_quit()
        print "leaving..."
  
    def on_ButtonScan_clicked(self, widget, data=None):
        self.on_ButtonSend_clicked(0, "_scan")

    def on_ButtonMsp430_clicked(self, widget, data=None):
        self.on_ButtonSend_clicked(0, "_msp430")
        
    def on_window_key_press_event(self, widget, event):
        key =  gtk.gdk.keyval_name(event.keyval)
        if key == "Return":
            self.on_ButtonYes_clicked(0, None)
        elif key == "space":
            self.on_ButtonNo_clicked(0, None)

    def on_ToggleButtonOfDebug_toggled(self, widget, data=None):
        self.FrameOfDebug.set_visible(not self.FrameOfDebug.get_visible())   
        self.EntryOfCommand.grab_focus()
                         
    def on_ButtonStart_clicked(self, widget, data=None):     
        #voltage = self.ComboBoxOfVoltage.get_active_text()
        #self.on_ButtonSend_clicked(0, '_start ' + voltage)
        file = self.FileChooserButtonOfTestMode.get_filename()
        if file != None:
            filename, fileext = os.path.splitext(file)
            if fileext == ".cali":
                self.on_ButtonSend_clicked(0, "_batch " + self.FileChooserButtonOfTestMode.get_filename())
            elif fileext == ".bas":
                self.on_ButtonSend_clicked(0, "_ply " + self.FileChooserButtonOfTestMode.get_filename())

    def on_ButtonStop_clicked(self, widget, data=None):
        if self.ThreadOfPly != None and self.ThreadOfPly.is_alive():
            self.on_ButtonSend_clicked(0, '_stop')
    
    def on_ButtonYes_clicked(self, widget, data=None):
        if self.ThreadOfPly != None and self.ThreadOfPly.is_alive():
            self.on_ButtonSend_clicked(0, '_yes')
            
    def on_ButtonNo_clicked(self, widget, data=None):
        if self.ThreadOfPly != None and self.ThreadOfPly.is_alive():
            self.on_ButtonSend_clicked(0, '_no')            
        
    def on_ComboBoxOfUart_changed(self, widget):
        self.serial_close_all()                
        model = self.ComboBoxOfUart.get_model()
        active = self.ComboBoxOfUart.get_active()
        port = model[active][0]

        if port != "NONE":
            baudrate = model[active][1]
            self.serial_connect(port, baudrate)
            self.EntryOfCommand.grab_focus()
        
    def on_TextOfLog_size_allocate(self, widget, event, data=None):
        adj = self.ScrolledWindowOfLog.get_vadjustment()
        adj.set_value(adj.upper - adj.page_size)
    
    def on_FileChooserButton_file_set(self, widget):
        file = self.FileChooserButton.get_filename()
        filename, fileext = os.path.splitext(file)

        if fileext == ".cali":
            self.EntryOfCommand.set_text("_batch " + self.FileChooserButton.get_filename())
        elif fileext == ".bas":
            self.EntryOfCommand.set_text("_ply " + self.FileChooserButton.get_filename())

        self.EntryOfCommand.grab_focus()
 
    def on_ButtonSend_clicked(self, widget, cmd=None):        
        if cmd == None:
            cmd = self.EntryOfCommand.get_text()
       
        if not cmd.isspace() and cmd != '':
            cmd = cmd.split()
            cmd[0] = cmd[0].lower()
            if cmd[0].startswith('_'):  # local and mcu's command
                if cmd[0] == '_clear':
                    if self.ThreadOfPly == None or not self.ThreadOfPly.is_alive():    # avoid accessing the shared resource: CONSOLE
                        #self.TextBufferOfLog.set_text('')
                        start, end = self.TextBufferOfLog.get_bounds()
                        self.TextBufferOfLog.delete(start, end)
                elif cmd[0] == '_ver':
                    self.TextBufferOfLog.insert_at_cursor(self.window.get_title() + '\n')
#                elif cmd[0] == '_start':
#                    if len(cmd) > 1:
#                        if cmd[1].isdigit():
#                            voltage = (int(cmd[1]) + 4) / 5 * 5
#                            self.TextBufferOfLog.insert_at_cursor("Start to calibrate at " + str(voltage) + "mV.\n")
#                            self.ButtonResultByColor.set_color(gtk.gdk.Color('green'))
                elif cmd[0] == '_scan': # should be deleted before release.
                    #Thread(target=cali_scan.CaliScan(self.ListStoreOfScan, self.ListOfPrinterSettings).run, args=(self.window, )).start()
                    #time.sleep(0.1)
                    cali_scan.CaliScan(scan_portlist = self.ListStoreOfScan, 
                                       printer_settings_mutable = self.ListOfPrinterSettings
                                       ).run(parent_window = self.window)       
                elif cmd[0] == '_msp430': # should be deleted before release.
                    cali_msp430.Msp430(portlist = self.ListStoreOfScan).run(parent_window = self.window)                                                               
                elif cmd[0] == '_stop':
                    self.set_check_status(0x80000000)                    
                    self.TextBufferOfLog.insert_at_cursor("The calibration process is stopped.\n")
                elif cmd[0] == '_yes':
                    self.set_check_status(0)
                elif cmd[0] == '_no':
                    self.set_check_status(1)
                elif cmd[0] == '_batch':
                    if len(cmd) > 1:
                        if os.path.isfile(cmd[1]):
                            self.TextBufferOfLog.insert_at_cursor("Batch processing with file " + cmd[1] + '\n')
                            file = open(cmd[1], 'r')
                            self.cmds = file.readlines()
                            file.close() 
                        else:
                            self.cmds = [cmd[1]]   
                           
                        self.ply_need_start = 1
                        self.ply_mode = 0   
                elif cmd[0] == '_ply':
                    if len(cmd) > 1:
                        if os.path.isfile(cmd[1]):
                            self.TextBufferOfLog.insert_at_cursor("PLY processing with file " + cmd[1] + "\n")
                            self.cmds = cmd[1]
                            self.ply_need_start = 1
                            self.ply_mode = 1
                                                          
            else:   # device's command
                model = self.ComboBoxOfUart.get_model()
                active = self.ComboBoxOfUart.get_active()
                
                port = model[active][0]
                if port != "NONE":
                    if self.ser[port][0] != None: 
                        text = ''
                        for command in cmd:
                            text += command
                            text += ' '
                        self.ser[port][0].write(text.rstrip() + "\n")
                        time.sleep(0.2) # make sure the command is sent completely
                    
            #self.EntryOfCommand.set_text("")
            if self.FrameOfDebug.get_visible():
                self.EntryOfCommand.grab_focus()
                
    def on_ButtonClear_clicked(self, widget):
        self.on_ButtonSend_clicked(0, '_clear')
           
    def on_EntryOfCommand_activate(self, widget):
        self.on_ButtonSend_clicked(widget)
        
    def receiving(self, port, rates):    # device's feedback

        print "thread receiving starts..\n"
        line = ''
        while True:
            if(self.ply_need_start == 1):
                if self.ThreadOfPly == None or not self.ThreadOfPly.is_alive():
                    self.ThreadOfPly = Thread(target=self.plying, args=(port, self.ply_mode,))
                    self.ThreadOfPly.start()
                    time.sleep(0.1)
                    self.ThreadOfPly.join()
                self.ply_need_start = 0    
                
            self.mutex.acquire()  
            ser_is_alive = self.ser[port][0]
            self.mutex.release()
            if(ser_is_alive != None):
                try:
                    left = self.ser[port][0].inWaiting()
                    
                except serial.serialutil.SerialException:
                    self.serial_close_all()
                    gtk.threads_enter()
                    self.TextBufferOfLog.insert_at_cursor("\nPlease connect the serial device and reboot the program.\n")
                    gtk.threads_leave()
                else:
                    if left > 0 :
                        line += self.ser[port][0].read(left)   
                        if line != '' :
                            gtk.threads_enter()
                            self.TextBufferOfLog.insert_at_cursor(line)
                            gtk.threads_leave()
                        line = ''
                
            else:
                print "thread receiving exit.."
                break
                #todo: need usb plug/unplug signal
            
            time.sleep(0.01)    # avoid too much cpu resource cost

    def batching(self, port, cmd, check_mode):
        print "thread batching starts...\n"
        
        self.ser[port][0].flushInput()
        self.ser[port][0].flushOutput()
        
        #for cmd in self.cmds:
        cmd = cmd.strip()
        self.ser[port][0].write(cmd + "\n")
        if check_mode == "AUTO":
            while True:
                ch = self.ser[port][0].read(1)                
                if ch.isdigit() or self.batch_is_timeout == 1:
                    break

        if self.batch_is_timeout == 1:
            self.batch_is_timeout = 0
            ch = '1'
            print "thread batching is timeout."
        else:
            time.sleep(0.5)
            if check_mode == "AUTO":
                self.ser[port][0].flushInput()
                if ch == '0':
                    self.set_check_status(0)
                    text = " is succeed\n"
                else:
                    self.set_check_status(1)
                    text = " is failed\n"      
                #gtk.threads_enter()
                self.TextBufferOfLog.insert_at_cursor(cmd.upper() + text)
                #gtk.threads_leave()              
            else:
                line = ""
                left = self.ser[port][0].inWaiting()
                if left > 0:
                    line += self.ser[port][0].read(left)   
                    if line != '' :
                        gtk.threads_enter()
                        self.TextBufferOfLog.insert_at_cursor(line)
                        gtk.threads_leave()

    def plying(self, port=0, method=0):   # 0: line by line 1: Lex-Yacc method    

        print "thread plying starts.."
        self.check_status = 2
                
        if method == 0:
            for cmd in self.cmds:
                if self.ThreadOfBatch == None or not self.ThreadOfBatch.is_alive():
                    self.ThreadOfBatch = Thread(target=self.batching, args=(port, cmd, "AUTO"))
                    self.ThreadOfBatch.start()
                    time.sleep(0.1)
                    self.ThreadOfBatch.join(1)  # 1) join() only waits for a thread to finish. it won't make executing any thread.
                                                # 2) join(timieout) will stop blocking after timeout, but will not terminate the thread if it is still running.
                    if self.ThreadOfBatch.is_alive():
                        self.batch_is_timeout = 1
                    print 'batching ended'
                else:
                    print "batching is in use"
                if self.get_check_status() != 0:
                    #self.check_status = 2
                    break
                #time.sleep(0.01)
        else:
            prog = basparse.parse(open(self.cmds).read())
            if not prog: print "basparse import error."
            try:
                basinterp.BasicInterpreter(prog, self).run()
            except RuntimeError:
                print "basinterp error"  
    
    def get_check_status(self):        
        return self.check_status
    
    def set_check_status(self, status):
        #if self.ThreadOfPly != None and self.ThreadOfPly.is_alive():
        if status == 0:
            self.ButtonResultByColor.set_color(gtk.gdk.Color('green'))
        elif status != 2:
            self.ButtonResultByColor.set_color(gtk.gdk.Color('red'))
        self.check_status &= 0x80000000
        self.check_status |= status
    
    def set_console_text(self, str=None):
        gtk.threads_enter()
        if str == None:
            start, end = self.TextBufferOfLog.get_bounds()
            self.TextBufferOfLog.delete(start, end)
        else:
            self.TextBufferOfLog.insert_at_cursor(str + "\n")
        gtk.threads_leave()
    
    def set_uart_text(self, port, rates, cmd, check_mode):
        if self.ser[port][0] == None or not self.ser[port][0].isOpen():
            self.serial_connect(port, rates)
        elif self.ser[port][1] != rates:
            self.serial_close_all()
            self.serial_connect(port, rates)
        
#        if check_mode == "AUTO": # auto check
        if self.ThreadOfBatch == None or not self.ThreadOfBatch.is_alive():
            #self.cmds = [str]
            self.ThreadOfBatch = Thread(target=self.batching, args=(port, cmd, check_mode))
            self.ThreadOfBatch.start()
            time.sleep(0.1)
            self.ThreadOfBatch.join(1) 
            if self.ThreadOfBatch.is_alive():
                self.batch_is_timeout = 1
        else:
            print "thread batch is in use.."
#        else: # manually check
#            self.ser[port][0].write(cmd + "\n")
    
    def set_tutorial(self, src):
        if(os.path.isfile(src)):
            ext = (src.split('.')[1]).upper()
            if ext == "JPG" or ext == "BMP" or ext == "PNG":
                self.ImageOfTutorial.set_from_file(src)
      #  self.ImageOfTutorial.set_from_file("xx.jpg")
        
    def ComboxOfUart_init(self):
        self.ser = {}   #{reference, instance, is_alive}
        ports = sorted(comports())
        
        while self.ComboBoxOfUart.get_active() != -1:
            self.ComboBoxOfUart.remove_text(self.ComboBoxOfUart.get_active())
        
        port_num = 0
        for port, desc, hwid in ports:
            self.ListStoreOfUart.append([port, '115200'])
            self.ListStoreOfUart.append([port, '9600'])
            self.ListStoreOfScan.append([port, '1200'])
            self.ser[port] = None, 0          
            port_num += 1 
            
        if port_num == 0 :
            self.ComboBoxOfUart.insert_text(0, "NONE")
            
        self.ComboBoxOfUart.set_active(0)
        
    def serial_connect(self, port, rates):
        try: 
            self.ser[port] = serial.Serial(port, rates, timeout=1), rates
        except serial.serialutil.SerialException:
            self.ser[port] = None, 0
            #self.ser_is_alive = 0
            print "serial error"
        else:
            time.sleep(0.3) # under raspberry pi, we need to wait until thread receiving quits successfully.
            if self.ThreadOfReceiving == None or not self.ThreadOfReceiving.is_alive():
                self.ThreadOfReceiving = Thread(target=self.receiving, args=(port, rates,))                  
                self.ThreadOfReceiving.start()
                #self.thread.join()     # this will block current thread (Main)
                time.sleep(0.1) # to make sure the new thread is created successfully.    
    
    def serial_close_all(self):
        for port in self.ser:
            if self.ser[port][0] != None:   # and self.ser[port][0].isOpen():
                self.mutex.acquire()    # to avoid mis-judging in thread receiving - ser.inWaiting()
                self.ser[port][0].close()
                self.ser[port] = None, 0
                self.mutex.release()
                       
    def __init__(self):
        builder = gtk.Builder()
        builder.add_from_file("calibration.glade")
        builder.connect_signals(self)
        
        self.ButtonResultByColor = builder.get_object("ButtonResultByColor")
        self.ButtonYes = builder.get_object("ButtonYes")
        self.ButtonNo = builder.get_object("ButtonNo")
        self.ButtonPrinting = builder.get_object("ButtonPrinting")
        self.ButtonYes.child.modify_font(pango.FontDescription("sans 48"))
        self.ButtonNo.child.modify_font(pango.FontDescription("sans 48"))
        self.ListStoreOfUart = builder.get_object("liststore2")
        self.ListStoreOfScan = builder.get_object("liststore3")
        self.ComboBoxOfUart = builder.get_object("ComboBoxOfUart")
        self.window = builder.get_object("window")
        
    
        self.TextBufferOfLog = builder.get_object("textbuffer1")
        self.EntryOfCommand = builder.get_object("EntryOfCommand")
        self.ScrolledWindowOfLog = builder.get_object("ScrolledWindowOfLog")
        self.FileChooserButton = builder.get_object("FileChooserButton")
        self.FileChooserButtonOfTestMode = builder.get_object("FileChooserButtonOfTestMode")
        self.FileFilterForView = builder.get_object("filefilter1")
        self.FileFilterForView.add_pattern("*.cali")
        self.FileFilterForView.add_pattern("*.bas")
        self.ImageOfTutorial = builder.get_object("ImageOfTutorial") 
        self.FrameOfDebug = builder.get_object("FrameOfDebug")
        
        self.ListOfPrinterSettings = [None]
        # init for multiple threading        
        self.ply_need_start = 0
        self.ply_mode = 0   # 0: line by line 1: yacc mode
        self.batch_is_timeout = 0
        self.check_status = 2   # 2: init value, not checked 
                                # 1: failed 
                                # 0: success 
                                # 0x8000000x: stopped
        self.ThreadOfReceiving = None    
        self.ThreadOfPly = None 
        self.ThreadOfBatch = None
        self.mutex = threading.Lock() 
        
        self.ComboxOfUart_init()
        
        self.window.show_all()

    def main(self):
        gtk.gdk.threads_init()
        gtk.threads_enter()
        gtk.main()
        gtk.threads_leave()
        
if __name__ == "__main__":
    cali = CaliTest()
    cali.main()
    
