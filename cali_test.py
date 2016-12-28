#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import pango
import threading
from threading import Thread
import serial
import time
import datetime
import re
import os
#import usb.core
#import usb.util
#import chardet

#import basiclex
#import basparse
#import basinterp

#import cali_scan
#import cali_msp430
#if os.name == 'posix' :
#    import pexpect
#else:
#    import subprocess
    
if os.name == 'nt' :
    from serial.tools.list_ports_windows import *
elif os.name == 'posix' :
    from serial.tools.list_ports_posix import *
    import RPi.GPIO as GPIO
else :
    raise ImportError("Sorry: no implementation for your platform ('%s') available" % (os.name,))

class CaliTest:
    def ConvertCN(self, s):  
        return s.encode('gb18030')  
    
    def timer_event(self):
        if self.led_check_status > 1:
            if self.ThreadOfPly != None and self.ThreadOfPly.is_alive():   # and self.check_status != 0x80000000:
                self.set_check_status_led((self.led_check_status & 2) + 2)
                t = threading.Timer(1, self.timer_event)
                t.start()
            else:
                self.set_check_status_led()            
    
    def on_FileChooserButtonOfTestMode_selection_changed(self, widget, data=None):
        # TODO:  1. There are 3 events happened at init
        #        2. No need to write configure file even the filename is not changed.
        try:
            with open("./cali.conf", "w") as f:
                content = "DEFAULT_SCRIPT=" + str(self.FileChooserButtonOfTestMode.get_filename())
                f.write(content)
        except:
            print "cali.conf create failed."
        self.EntryOfSerialNumber.grab_focus()
        
    #def on_window_expose_event(self, widget, data=None):
    #    self.EntryOfSerialNumber.grab_focus()
        
    def on_window_destroy(self, widget, data=None):
        self.on_ButtonSend_clicked(0, "_stop")
        self.serial_close_all()
        gtk.main_quit()
        print "leaving...\n"
  
    def on_ButtonScan_clicked(self, widget, data=None):
        self.on_ButtonSend_clicked(0, "_scan")

    def on_ButtonMsp430_clicked(self, widget, data=None):
        self.on_ButtonSend_clicked(0, "_msp430")
        
    def on_window_key_press_event(self, widget, event):
        key = gtk.gdk.keyval_name(event.keyval)
        if key == "F1":
            self.on_ButtonYes_clicked(0, None)
        elif key == "F2":
            self.on_ButtonNo_clicked(0, None)
        elif key == "Return":
            self.on_ButtonSend_clicked(0, None)

    def on_ToggleButtonOfDebug_toggled(self, widget, data=None):
        self.FrameOfDebug.set_visible(not self.FrameOfDebug.get_visible())
        self.HboxOfPassFail.set_visible(not self.HboxOfPassFail.get_visible())   
        self.EntryOfCommand.grab_focus()
                         
    def on_ButtonStart_clicked(self, widget, data=None):     
        #serial_number = self.EntryOfSerialNumber.get_text()
        #if not serial_number.isdigit():
        #    self.insert_into_console("Please scan barcode first.\n")
        #    self.EntryOfSerialNumber.grab_focus()
        #    return 
        #self.serial_number = serial_number
        file = self.FileChooserButtonOfTestMode.get_filename()
        if file != None:
            filename, fileext = os.path.splitext(file)
            if fileext == ".cali":
                self.on_ButtonSend_clicked(0, "_batch " + self.FileChooserButtonOfTestMode.get_filename())
            elif fileext == ".bas":
                self.on_ButtonSend_clicked(0, "_ply " + self.FileChooserButtonOfTestMode.get_filename())
        self.EntryOfSerialNumber.grab_focus()

    def on_ButtonStop_clicked(self, widget, data=None):
        if self.ThreadOfPly != None and self.ThreadOfPly.is_alive():
            self.on_ButtonSend_clicked(0, '_stop')
        self.EntryOfSerialNumber.grab_focus()
    
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
        
    def on_TextViewOfLog_size_allocate(self, widget, event, data=None):
        adj = self.ScrolledWindowOfLog.get_vadjustment()
        #adj.set_value(adj.upper - adj.page_size)
        gobject.idle_add(adj.set_value, (adj.upper - adj.page_size))
        
    def on_FileChooserButton_file_set(self, widget):
        file = self.FileChooserButton.get_filename()
        filename, fileext = os.path.splitext(file)

        if fileext == ".cali":
            self.EntryOfCommand.set_text("_batch " + self.FileChooserButton.get_filename())
        elif fileext == ".bas":
            self.EntryOfCommand.set_text("_ply " + self.FileChooserButton.get_filename())

        self.EntryOfCommand.grab_focus()
 
    def on_ButtonSend_clicked(self, widget, cmd=None, para=None):        
        if cmd == None:
            cmd = self.EntryOfCommand.get_text()
       
        if not cmd.isspace() and cmd != '':
            cmd = cmd.split()
            cmd[0] = cmd[0].lower()
            if cmd[0].startswith('_'):  # local and mcu's command
                if cmd[0] == '_clear':
                    #if self.ThreadOfPly == None or not self.ThreadOfPly.is_alive():    # avoid accessing the shared resource: CONSOLE
                    start, end = self.TextBufferOfLog.get_bounds()
                    gobject.idle_add(self.TextBufferOfLog.delete, start, end)
                elif cmd[0] == '_ver':
                    self.insert_into_console(self.window.get_title() + '\n')
#                elif cmd[0] == '_start':
#                    if len(cmd) > 1:
#                        if cmd[1].isdigit():
#                            voltage = (int(cmd[1]) + 4) / 5 * 5
#                            self.TextBufferOfLog.insert_at_cursor("Start to calibrate at " + str(voltage) + "mV.\n")
#                            self.ButtonResultByColor.set_color(gtk.gdk.Color('green'))
                elif cmd[0] == '_scan': # should be deleted before release.
                    import cali_scan
                    #Thread(target=cali_scan.CaliScan(self.ListStoreOfScan, self.ListOfPrinterSettings).run, args=(self.window, )).start()
                    #time.sleep(0.1)
                    start, end = self.TextBufferOfLog.get_bounds()
                    cali_scan.CaliScan(printer_settings_mutable = self.ListOfPrinterSettings, console_log = self.TextBufferOfLog.get_text(start, end), cert_format=para, sn_len=self.sn_len).run(parent_window = self.window)
                elif cmd[0] == '_msp430': # should be deleted before release.
                    import cali_msp430
                    cali_msp430.Msp430().run(parent_window = self.window)                                                               
                elif cmd[0] == '_stop':
                    self.condition.acquire()
                    self.condition.notifyAll()
                    self.condition.release()
                    self.set_check_status(0x80000000)                    
                    self.insert_into_console("The calibration process is stopped.\n")
                elif cmd[0] == '_yes':
                    self.condition.acquire()
                    #print "cond acquired"
                    if self.get_check_status() != 0:    # avoid twice key-event issue in Linux
                        self.set_check_status(0)
                    if self.get_ack_to_plying() != 0:
                        self.set_ack_to_plying(0)
                    #print "cond notifying"
                    self.condition.notifyAll()
                    self.condition.release()
                    #print "cond notified and released"                    
                elif cmd[0] == '_no':
                    self.condition.acquire()
                    #print "cond_ acquired"                    
                    if self.get_check_status() != 1:
                        self.set_check_status(1)
                    if self.get_ack_to_plying() != 0:
                        self.set_ack_to_plying(0)
                    #print "cond_ notifying"
                    self.condition.notifyAll()
                    self.condition.release()
                    #print "cond_ notified and released"
                elif cmd[0] == '_batch':
                    if len(cmd) > 1:
                        if os.path.isfile(cmd[1]):
                            self.insert_into_console("Batch processing with file " + cmd[1] + '\n')
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
                            if self.ThreadOfSerialReceiving == None or not self.ThreadOfSerialReceiving.is_alive():
                                self.insert_into_console("Please check the UART connection and restart the program.\n")
                                self.set_check_status(1)
                            else:
                                self.insert_into_console("PLY processing with file " + cmd[1] + "\n")
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
                        text = self.encode_modbus_debug_cmd(port, cmd)  
                        print("DebugSerialSending: " + text)                                                                    
                        time.sleep(0.2) # make sure the command is sent completely
                    
                        self.set_ack_to_plying(0)
            #self.EntryOfCommand.set_text("")
            if self.FrameOfDebug.get_visible():
                self.EntryOfCommand.grab_focus()
                
    def on_ButtonClear_clicked(self, widget):
        self.on_ButtonSend_clicked(0, '_clear')
           
    def on_EntryOfCommand_activate(self, widget):
        self.on_ButtonSend_clicked(widget)
                    
    def serialReceiving(self, port, rates):    # device's feedback
        print "thread serialReceiving starts..\n"
        line = ''
        lastLeft = 0
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
                    ###gtk.threads_enter()
                    self.insert_into_console("\nPlease connect the serial device and reboot the program.\n")
                    ###gtk.threads_leave()
                else:
                    if ((left > 0) and (self.get_ack_to_plying() == 0)):
                        if (lastLeft == left) :
                            line += self.ser[port][0].read(left)   
                            if line != '' :
                                ###gtk.threads_enter()
                                encodeline = line.encode("hex")                                
                                self.serial_crc_valid(len(line),encodeline)
                                print("serialReceiving: " + encodeline + "\n")
                                ###gtk.threads_leave()
                                line = ''
                        lastLeft = left
                
            else:
                print "thread serial receiving exit..\n"
                break
                #todo: need usb plug/unplug signal
            
            time.sleep(0.1)    # avoid too much cpu resource cost, change from 0.01 to 0.1 for slower than the serial communication speed, then can output the whole command one time.
            
    def get_batching_result(self, keywords):
        print 'get', keywords
        print "in", self.batching_result
        #keywords = keywords.upper()
        result = "None"
        if keywords in self.batching_result:
            result = self.batching_result[keywords]
            #del self.batching_result[keywords]    #may cause glibc "double free" bug.
            self.batching_result[keywords] = "None"
            result = result.strip() #remove leading/ending spaces
            regular = re.compile(r'[-+]?[0-9]+\.?[0-9]*$')   # match numbers
            #if regular.match(result) != None:
            #    result = float(result)
        return result
    
    def set_batching_result(self, data_with_2line):
        print "set, ", data_with_2line
        if len(data_with_2line) > 1:
            self.batching_result[data_with_2line[0]] = data_with_2line[1]
               
    def batching(self, port, cmd, check_mode):
        print "thread batching starts...\n"
                
        self.ser[port][0].flushInput()
        self.ser[port][0].flushOutput()              

        #for cmd in self.cmds:
        cmd = cmd.strip()
        cmd_split = cmd.split(' ')
        text = ''
        text = self.encode_modbus_debug_cmd(port, cmd_split)
        print("Batching send to slave : " + text + "\n")       
        
        time.sleep(0.1)
        left = self.ser[port][0].inWaiting()
        line = ''
        inter = []
        resend_times = 0
        timeout_times = 0
        while (resend_times < self.MB_RESEND_TIMES):
            if left > 0:
                line += self.ser[port][0].read(left)    
                if line != '' :
                    encodeline = line.encode("hex")
                    print("Batching reply from slave: " + encodeline + "\n")
                    batchingitem = []
                    batchingitem.append(cmd)
                    batchingitem.append(encodeline)
                    self.set_batching_result(batchingitem)
                    self.serial_crc_valid(len(line),encodeline)                                                            
                    line = encodeline = ''
                break;
            else:
                if (timeout_times > self.MB_TIMEOUT_TIMES):                    
                    text = self.encode_modbus_debug_cmd(port, cmd_split)
                    resend_times = resend_times + 1
                    timeout_times = 0
                    time.sleep(0.1)
                    print("Batching send to slave again: " + text + "\n")  
                else:
                    time.sleep(0.1)
                    timeout_times = timeout_times + 1
        if (left <= 0):
            self.set_console_text("Batching: %s, " %port + "No response from slave")
            
        self.ack_to_plying = 0   
        self.ser[port][0].flushInput()
        print "thread batching stopped.\n"

    def plying(self, port=0, method=0):   # 0: line by line 1: Lex-Yacc method    

        print "thread plying starts.."
        self.clear_status()  
        self.timer_event()     
        if method == 0:
            for cmd in self.cmds:
                if self.ThreadOfBatch == None or not self.ThreadOfBatch.is_alive():
                    self.ThreadOfBatch = Thread(target=self.batching, args=(port, cmd, "AUTO"))
                    self.ThreadOfBatch.start()
                    time.sleep(0.2)
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
            import basparse
            import basinterp
            prog = basparse.parse(open(self.cmds).read())
            if not prog: 
                self.set_console_text("*.BAS script basparse import error.")
                self.set_check_status(1)
            else:
                try:
                    basinterp.BasicInterpreter(prog, self).run()
                except RuntimeError:
                    self.set_console_text("*.BAS script basinterp error.")
                    self.set_check_status(1)

        CERT_VALUE = datetime.datetime.now()
        CERT_VALUE = CERT_VALUE.strftime("%Y-%m-%d %H:%M:%S")  
        if self.get_check_status() == 0:
            filename = "PASS"
        else:
            filename = "FAIL"              
        filename = str(self.serial_number) + filename + str(CERT_VALUE)
        filename = re.sub(r'[^a-zA-Z0-9]', '', filename)
        time.sleep(1)
        start, end = self.TextBufferOfLog.get_bounds()
        console_log = self.TextBufferOfLog.get_text(start, end)
        
        if self.save_to_log('./certification/', filename, console_log) == 1:
            self.set_console_text("LOG failed.")    
            self.set_check_status_led(1)
        else:
            self.set_check_status_led()

        self.batching_result = {}
        #gtk.threads_enter()                    
        gobject.idle_add(self.EntryOfSerialNumber.set_text, '')
        gobject.idle_add(self.EntryOfSerialNumber.grab_focus)
        #gtk.threads_leave()
        print "thread plying stopped"
        
    def save_to_log(self, directory, filename, logcontent):
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)        
            
            logfile = None
            logfile = open(directory + filename + ".log", 'w')
            logfile.write(logcontent)
        except:
            if logfile != None:
                logfile.close()
            return 1
        finally:
            return 0
            logfile.close()
                    
    def get_check_status(self):  
        #self.mutex_of_checkstatus.acquire()  
        status = self.check_status
        #self.mutex_of_checkstatus.release()    
        return status
    
    def set_check_status(self, status):
        #self.mutex_of_checkstatus.acquire()
        self.check_status &= 0x80000001
        self.check_status |= status
       # self.mutex_of_checkstatus.release()
    
    def get_ack_to_plying(self):
        #self.mutex_of_plyack.acquire()
        ack = self.ack_to_plying
        #self.mutex_of_plyack.release()
        return ack
    
    def set_ack_to_plying(self, ack):
        #self.mutex_of_plyack.acquire()
        self.ack_to_plying = ack
        #self.mutex_of_plyack.release()
        
    def clear_status(self):
        self.check_status = 0
        self.set_check_status_led(2)
         
    def set_check_status_led(self, status=None):
        if status == None:
            status = self.get_check_status()
        
        if status == 0:
            color = 'green'
        elif status == 1:
            color = 'red'
        elif status == 2:
            color = 'gray'            
        else:
            color = 'yellow'
        self.led_check_status = status
        self.ButtonResultByColor.set_color(gtk.gdk.Color(color))
        
    def set_console_text(self, cmd=None):
        ###gtk.threads_enter()
        if cmd == "_CLEAR":
            #start, end = self.TextBufferOfLog.get_bounds()
            #gobject.idle_add(self.TextBufferOfLog.delete, start, end)
            self.on_ButtonSend_clicked(0, "_clear")
        elif cmd == "_CURRENTTIME":
            self.insert_into_console((datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '\n'))
        elif cmd == "_ERROR":
            self.set_check_status(1)
        elif cmd == "_GETERRORCODE":
            data_with_2line = ('_GETERRORCODE ' + str(self.get_check_status())).split()
            self.set_batching_result(data_with_2line)
        elif cmd == "_YES":
            gobject.idle_add(self.on_ButtonSend_clicked, 0, '_yes')
        elif cmd == "_NO":
            gobject.idle_add(self.on_ButtonSend_clicked, 0, '_no')
        elif cmd == '_SCAN':
            #self.on_ButtonSend_clicked(0, '_scan')
            gobject.idle_add(self.on_ButtonSend_clicked, 0, '_scan')
        elif cmd == '_SCANEC':
            gobject.idle_add(self.on_ButtonSend_clicked, 0, '_scan', 'EC')
        elif cmd == '_SCANPH':
            gobject.idle_add(self.on_ButtonSend_clicked, 0, '_scan', 'PH')
        elif cmd == "_BARCODE":
            self.serial_number = self.EntryOfSerialNumber.get_text()
            if not self.serial_number.isdigit():
                self.serial_number = "1234567890"
            data_with_2line = ('_BARCODE ' + self.serial_number).split()
            self.set_batching_result(data_with_2line)
        elif cmd.startswith("_BARCODELEN="):
            sn_len = cmd.split('=')[1]
            if sn_len.isdigit():
                self.sn_len = int(sn_len)
        elif cmd == '_MSP430':
            self.on_ButtonSend_clicked(0, '_msp430')
        elif cmd == '_PORTCOUNT':
            data_with_2line = ('_PORTCOUNT ' + str(len(self.ser))).split()
            self.set_batching_result(data_with_2line)
        elif cmd.startswith("_UARTOPEN"):            
            paras = cmd.lstrip('_UARTOPEN').strip()
            if len(paras) > 0:
                port = None
                baudrate = 9600
                parity = "N"
                check = "AUTO"
                
                paras = paras.split(',')
                for par in paras:
                    arg = par.split('=')
                    if len(arg) > 1:
                        if arg[0] == "PORT":
                            port = arg[1].strip()
                        elif arg[0].startswith("BAUD"):
                            baudrate = int(arg[1].strip())
                        elif arg[0].startswith("PARI"):
                            parity = arg[1].strip()
                        elif arg[0] == "CHECK":
                            check = arg[1].strip()
                            
                print port, baudrate, parity, check
                if port != None:
                    uart_conn_result = self.set_uart_text(port, baudrate, None, check, parity)
                    if uart_conn_result == 0:
                        data_with_2line = ('_UARTOPEN ' + str(port)).split()
                        self.set_batching_result(data_with_2line)
                
                
        elif cmd.startswith('_UARTCLOSE'):
            port = cmd.lstrip('_UARTCLOSE').strip()
            if port in self.ser:
                if self.ser[port][0] != None:   # and self.ser[port][0].isOpen():
                    self.mutex.acquire()    # to avoid mis-judging in thread receiving - ser.inWaiting()
                    self.ser[port][0].close()
                    self.ser[port] = None, 0
                    self.mutex.release()
        else:
            import chardet
            cmd = cmd.decode(chardet.detect(cmd)['encoding'])  # decode() means decode the wanted format to unicode format.
            self.insert_into_console(cmd + "\n")
        ###gtk.threads_leave()
    
    def insert_into_console(self, cmd=None):
        if cmd != None:
            gobject.idle_add(self.TextBufferOfLog.insert_at_cursor, cmd)
                              
    def setup_serial(self, port, rates):   
        try:
            comport = self.ser[port]
        except KeyError:
            gobject.idle_add(self.set_console_text, "The COM port " + port + " is not existed.\n")
            self.set_check_status(2)
            return 1
        
        if comport[0] == None or not comport[0].isOpen():
            self.serial_connect(port, rates, parity)
        elif comport[1] != rates:
            self.serial_close_all()
            self.serial_connect(port, rates, parity)       
            
    def set_uart_text(self, port, rates, cmd=None, check_mode="AUTO", parity='N'):
        # TODO: disuse setup_serial, need check
        #self.setup_serial(port, rates)
        try:
            comport = self.ser[port]
        except KeyError:
            gobject.idle_add(self.set_console_text, "The COM port " + port + " is not existed.\n")
            self.set_check_status(2)
            return 1
            
        if comport[0] == None or not comport[0].isOpen():
            self.serial_connect(port, rates, parity)
        elif comport[1] != rates:
            self.serial_close_all()
            self.serial_connect(port, rates, parity)
#         if check_mode == "AUTO": # auto check
        if cmd != None: # in case a new uart connection request without command transferring.
            for i in range(1,3):
                if self.ThreadOfBatch == None or not self.ThreadOfBatch.is_alive():
                    print "batching times:", i
                    self.ThreadOfBatch = Thread(target=self.batching, args=(port, cmd, check_mode))
                    self.ThreadOfBatch.start()
                    time.sleep(0.8)
                    self.ThreadOfBatch.join(2) 
                    if self.ThreadOfBatch.is_alive():
                        self.batch_is_timeout = 1
                        time.sleep(4)
                    else:
                        break
                else:
                    print "thread batch is in use.."
                #        else: # manually check
                #            self.ser[port][0].write(cmd + "\n")
        return 0                        
                        
    
    def set_tutorial(self, src):
        src = './tutorials/' + src
        if(os.path.isfile(src)):
            ext = (src.rsplit('.', 1)[1]).upper()
            if ext == "JPG" or ext == "BMP" or ext == "PNG":
                gobject.idle_add(self.ImageOfTutorial.set_from_file, src)
                #  self.ImageOfTutorial.set_from_file("xx.jpg")
    
    def set_instruction(self, words):
        import chardet
        if words == None:
            words = ' '
        words = words.decode(chardet.detect(words)['encoding'])
        words = words.split('\\n')
        color_list = {'BLACK', 'RED', 'BLUE'}
        font_size = 22
        font_color = 'black'
        display_words = ''
        if len(words) > 1:            
            for word in words:
                if 'FONTCOLOR=' in word:
                    fcolor = word.split('=')[1].upper()
                    if fcolor in color_list:
                        font_color = fcolor
                elif 'FONTSIZE=' in word:
                    fsize = word.split('=')[1]
                    if fsize.isdigit():
                        font_size = fsize
                else:
                    display_words += word + '\n'
        else:
            display_words += words[0]
        gobject.idle_add(self.LabelOfInstruction.set_text, display_words)
        gobject.idle_add(self.LabelOfInstruction.modify_fg, gtk.STATE_NORMAL, gtk.gdk.color_parse(font_color))
        gobject.idle_add(self.LabelOfInstruction.modify_font, pango.FontDescription("sans " + str(font_size)))

# Ting start      
#     def flash_msp430(self, hexfile):
#         cmds = ['-eE', '-PV', '-r', '-i', 'ihex', hexfile]
#         jtagfile = './msp430-jtag.py'
#         if not os.path.isfile(jtagfile):
#             jtagfile = './msp430-jtag.pyc'
#         self.cmds = ['python', jtagfile, '--time', '-p']
#         if os.name == 'posix':
#             os.environ['LIBMSPGCC_PATH'] = '/usr/lib'
#             self.cmds.append('/dev/ttyACM0')
#         else:
#             self.cmds.append('TIUSB')
#             
#         self.cmds += cmds
#         
#         if os.name == 'posix':
#             command = ''
#             for cmd in self.cmds:
#                 command += cmd
#                 command += ' '
#             start_time = time.time()
#             import pexpect
#             child = pexpect.spawn(command)
#             result = ''
#             while True:
#                 try:       
#                     child.expect('\r')
#                     result += child.before
#                     #gtk.threads_enter()                    
#                     self.insert_into_console(child.before)
#                     #gtk.threads_leave()
#                 except:
#                     #gtk.threads_enter()
#                     self.insert_into_console("\nTime: " + str(time.time() - start_time) + 's\n')
#                     #gtk.threads_leave()
#                     break
#                 time.sleep(0.1)
#             
#         else:    
#             import subprocess    
#             proc = subprocess.Popen(self.cmds, 
#                             shell=False, 
#                             stderr=subprocess.PIPE)
#             ###gtk.threads_enter()
#             result = proc.communicate()[1]
#             self.insert_into_console(result)
#             ###gtk.threads_leave()
# 
#         if ('Erase check by file: OK' or 'Programming: OK' or 'Verify by file: OK') not in result:
#             #gtk.threads_enter()
#             self.insert_into_console("flash failed.\n")
#             ###gtk.threads_leave()
#             self.set_check_status(1)
# Ting end 

    def ComboxOfUart_init(self):
        self.ser = {}   #{reference, instance, is_alive}
        ports = sorted(comports())
        
        while self.ComboBoxOfUart.get_active() != -1:
            self.ComboBoxOfUart.remove_text(self.ComboBoxOfUart.get_active())
        
        port_num = 0
        for port, desc, hwid in ports:
            if port.find('ttyACM') == -1:
                self.ListStoreOfUart.append([port, '38400'])
                #self.ListStoreOfUart.append([port, '19200'])
                #self.ListStoreOfUart.append([port, '57600'])
                self.ser[port] = None, 0          
                port_num += 1 
                
        if port_num == 0 :
            self.ComboBoxOfUart.insert_text(0, "NONE")
            
        self.ComboBoxOfUart.set_active(0)
        
    def serial_connect(self, port, rates, parity="N"):
        try: 
            # TODO: need check 'E'
            #self.ser[port] = serial.Serial(port, rates, 8, 'E', timeout=1), rates
            self.ser[port] = serial.Serial(port, rates, parity=parity, timeout=1), rates
        except serial.serialutil.SerialException:
            self.ser[port] = None, 0
            #self.ser_is_alive = 0
            print "serial error"
        else:
            time.sleep(0.3) # under raspberry pi, we need to wait until thread serial receiving quits successfully.
            if self.ThreadOfSerialReceiving == None or not self.ThreadOfSerialReceiving.is_alive():
                self.ThreadOfSerialReceiving = Thread(target=self.serialReceiving, args=(port, rates,))                  
                self.ThreadOfSerialReceiving.start()
                #self.thread.join()     # this will block current thread (Main)
                time.sleep(0.1) # to make sure the new thread is created successfully.    
    
    def serial_close_all(self):
        for port in self.ser:
            if self.ser[port][0] != None:   # and self.ser[port][0].isOpen():
                self.mutex.acquire()    # to avoid mis-judging in thread serial receiving - ser.inWaiting()
                self.ser[port][0].close()
                self.ser[port] = None, 0
                self.mutex.release()
                
    def USB_init(self):
        # find our device
        dev = usb.core.find(idVendor=0x90C, idProduct=0x1000)          
            # was it found?
        if dev is None:
            raise ValueError('USB Device not found')
                      
        # set the active configuration. With no arguments, the first
        # configuration will be the active one
        dev.set_configuration()
        
        # get an endpoint instance
        cfg = dev.get_active_configuration()
        intf = cfg[(0,0)]

        ep = usb.util.find_descriptor(
            intf,
            # match the first OUT endpoint
            custom_match = \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_OUT)
        
        assert ep is not None
        
        # write the data
        #ep.write('test')

    def serial_crc16(self, pushMsg, usDataLen):    
        uchCRCHi = 0xFF
        uchCRCLo = 0xFF
        uIndex = 0
        i = 0
            
        while usDataLen:        
            uIndex = uchCRCHi ^ pushMsg[i]            
            uchCRCHi = uchCRCLo ^ self.auchCRCHi[uIndex]
            uchCRCLo = self.auchCRCLo[uIndex]
            usDataLen = usDataLen - 1
            i = i + 1
        else:
            return (uchCRCHi << 8 | uchCRCLo);

    def serial_crc_valid(self, lenline, encodeline): 
        inter= [] 
        for i in range(0,(lenline - 2)) :               
            inter.append(int(encodeline[(2*i):(2*i+2)], 16))
            
        crc16 = self.serial_crc16(inter, len(inter))
        if (int((encodeline[2*(lenline-2):2*lenline]),16) != crc16):
            self.set_console_text("reply from slave CRC error")
                                              
    def spi_send(self, value):
        # Value send
        for i in range(8):
            if (value & 0x80):
                GPIO.output(self.MOSI, GPIO.HIGH)
            else:
                GPIO.output(self.MOSI, GPIO.LOW)
            # Generate negative edge of the clock signal    
            GPIO.output(self.SCLK, GPIO.HIGH)
            time.sleep(0.000001)
            GPIO.output(self.SCLK, GPIO.LOW)
            value <<= 1 # Push the bit string one position to the left

    def mcp_spi_write(self, opcode, addr, data):
        #opcode = self.SPI_SLAVE_ADDR
        # self.CS activated (LOW-Activate)
        GPIO.output(self.CS, GPIO.LOW)
        self.spi_send(opcode|self.SPI_SLAVE_WRITE) # OP-Code send
        self.spi_send(addr)                   # Address send
        self.spi_send(data)                   # Data send
    
        # self.CS not active
        GPIO.output(self.CS, GPIO.HIGH) 
    
    def mcp_spi_read(self, opcode, addr):
        # self.CS activated (LOW-Activate)
        GPIO.output(self.CS, GPIO.LOW)
        
        self.spi_send(opcode|self.SPI_SLAVE_READ) # OP-Code send
        self.spi_send(addr)                  # Address send
        
        # Receiving data    
        value = 0
        for i in range(8):        
            value <<= 1 # Slide 1 position to the left
            if(GPIO.input(self.MISO)):
                value |= 0x01    
            # Generate Falling clock edge   
            GPIO.output(self.SCLK, GPIO.HIGH)
            GPIO.output(self.SCLK, GPIO.LOW)
    
        # self.CS not active
        GPIO.output(self.CS, GPIO.HIGH)
        return value
    
    def mcp_reset(self):
        GPIO.output(self.CE1,       GPIO.LOW)  
        GPIO.output(self.CE1,       GPIO.HIGH)
    
    def dac_spi_write(self, dac_slave_id, addr, data):  
        latch = self.daclatch[dac_slave_id - self.dac_start_id]    
        if (addr == self.DAC_ADDR_DATA):
            d_data = (int((data* 4096 * 16)/24) & 0xFFF0)  
        else:
            d_data = data
        # self.LATCH activated (LOW-Activate)
        GPIO.output(latch, GPIO.LOW)
        
        self.spi_send(addr)
        self.spi_send(d_data>>8)              
        self.spi_send(d_data)        
        time.sleep(0.000001)
        
        # self.LATCH not active
        GPIO.output(latch, GPIO.HIGH)
        
    def dac_spi_readback(self, dac_slave_id, read_addr):
        latch = self.daclatch[dac_slave_id - self.dac_start_id]      
        # self.LATCH activated (LOW-Activate)
        GPIO.output(latch, GPIO.LOW)
        
        # Readback 0x020001
        self.spi_send(self.DAC_ADDR_READBACK)
        self.spi_send(read_addr>>8)
        self.spi_send(read_addr)
        time.sleep(0.000001)
        
        # self.LATCH not active
        GPIO.output(latch, GPIO.HIGH)
        
        time.sleep(0.000001)
                
        # self.LATCH activated (LOW-Activate)
        GPIO.output(latch, GPIO.LOW)
            
        # Nop        
        # Receiving data    
        value = 0
        for i in range(24):   
            # Output Nop         
            GPIO.output(self.MOSI, GPIO.LOW)
            value <<= 1 # Slide 1 position to the left
            if(GPIO.input(self.MISO)):
                value |= 0x01
            # Generate Falling clock edge   
            GPIO.output(self.SCLK, GPIO.HIGH)
            GPIO.output(self.SCLK, GPIO.LOW)
                          
        # self.CS not active
        GPIO.output(latch, GPIO.HIGH)  
            
        return value
    
    def dac_reset(self):
        self.dac_spi_write(4, self.DAC_ADDR_RESET, self.DAC_RESET )
        self.dac_spi_write(5, self.DAC_ADDR_RESET, self.DAC_RESET )
        self.dac_spi_write(6, self.DAC_ADDR_RESET, self.DAC_RESET )
        self.dac_spi_write(7, self.DAC_ADDR_RESET, self.DAC_RESET )
        
    def encode_modbus_debug_cmd(self, port, cmd):  
        text = ''
        inter = []      
        for command in cmd :
            text += command
            inter.append(int(command, 16)) 
        crc16 = self.serial_crc16(inter, len(inter))    
        crc16list = []
        crc16list.append(hex((crc16&0xFF00)>>8).lstrip("0x"))
        crc16list.append(hex((crc16&0x00FF)).lstrip("0x"))
        for i in range(0,len(crc16list)):
            if int(crc16list[i],16) <= 0xF:
                cmd.append("0"+crc16list[i])
                text += ("0"+crc16list[i])
            else:
                cmd.append(crc16list[i])   
                text += crc16list[i]
        
        #self.ser[port][0].write(text.decode("hex").rstrip())                
        for command in cmd :
            self.ser[port][0].write(command.decode("hex"))
        return text
                
    def encode_modbus_cmd(self, slave_id, code, addr, length, *data):        
        if (code == self.MB_CODE_MULTI_WRITE):
            cmdinter = [slave_id, code, (addr&0xFF00) >> 8, (addr&0x00FF), (length&0xFF00) >> 8, (length&0x00FF), 2*length]
            for item in data[0]:
                cmdinter.append((item&0xFF00) >> 8)
                cmdinter.append(item&0xFF)
        else:    
            cmdinter = [slave_id, code, (addr&0xFF00) >> 8, (addr&0x00FF)]
            for databyte in data:
                cmdinter.append((databyte&0xFF00) >> 8)
                cmdinter.append(databyte&0xFF)
        crc16 = self.serial_crc16(cmdinter, len(cmdinter))  
        cmdinter.append((crc16&0xFF00)>>8)
        cmdinter.append(crc16&0x00FF)
        cmd = []
        for i in range(0,len(cmdinter)):
            cmdstrer = hex(cmdinter[i]).lstrip("0x")
            if cmdstrer == "":
                cmd.append("00")
            elif cmdinter[i] <= 0xF:
                cmd.append("0"+cmdstrer)
            else:
                cmd.append(cmdstrer)        
        return cmd      
    
    def decode_modbus_reply(self, code, data, rpl):                  
        if ((code == self.MB_CODE_SINGLE_WRITE) or (code == self.MB_CODE_MULTI_WRITE) or (code == self.MB_CODE_DIAGNOSTIC)):     
            response = int(rpl[8:(len(rpl)-4)], 16)  
        elif (code == self.MB_CODE_READ):   
            if (len(rpl[6:(len(rpl)-4)]) > 4):
                response = rpl[6:(len(rpl)-4)]   
            else:              
                response = int(rpl[6:(len(rpl)-4)], 16)  
        else:
            response = int(rpl, 16)   
            
        if ((code == self.MB_CODE_SINGLE_WRITE) and (response != data)):
            return (self.MD_UNEXPECTED, response) 
        else:
            return (self.MD_OK, response)   
        
    def modbus_ser_send(self, cmd, port, code):           
        self.ser[port][0].flushInput()
        self.ser[port][0].flushOutput()
        
        text = '' 
        for command in cmd:
            text += command
        #self.ser[port][0].write(text.decode("hex").rstrip())
        for i in range(0,len(cmd)):
            self.ser[port][0].write(cmd[i].decode("hex"))
        #if (code == self.MB_CODE_MULTI_WRITE):
        #    self.ser[port][0].write(text.decode("hex").rstrip())
        #else:
        #    for i in range(0,len(cmd)):
        #        self.ser[port][0].write(cmd[i].decode("hex"))
        if (self.modbus_log):
            print "MODBUS: %s, " %port + "send cmd to slave :", text    
                
    def modbus_command(self, port, slave_id, code, addr, data, length = 1, push_flag=0):      
        cmd = self.encode_modbus_cmd(slave_id, code, addr, length, data)  
        self.modbus_ser_send(cmd, port, code)
        
        time.sleep(0.1)
        resend_times = 0
        timeout_times = 0;
        while(resend_times < self.MB_RESEND_TIMES):
            left = self.ser[port][0].inWaiting()
            encodeline = line = ''
            if left > 0:
                line += self.ser[port][0].read(left)    
                if (line != ''):
                    encodeline = line.encode("hex")
                    if (self.modbus_log):
                        print("MODBUS: %s, " %port + "reply from slave  : " + encodeline + "\n")
                    if (push_flag):
                        batchingitem = []
                        batchingitem.append(cmd[0]+cmd[1]+cmd[2]+cmd[3]+cmd[4]+cmd[5])
                        batchingitem.append(encodeline)  
                        self.set_batching_result(batchingitem)
                    if (int(encodeline[2:4],16) > 0x80):
                        self.set_console_text("MODBUS: %s, " %port + "reply from slave exception, exception code %s" %encodeline[2:4])
                        return (self.MD_EXCEPTION, encodeline[2:4])
                    else:    
                        self.serial_crc_valid(len(line),encodeline)    
                break
            else:
                if (timeout_times > self.MB_TIMEOUT_TIMES):
                    self.modbus_ser_send(cmd, port, code)
                    time.sleep(0.1)
                    resend_times += 1
                    timeout_times = 0
                else:
                    time.sleep(0.1)
                    timeout_times = timeout_times + 1
                    
        if (left <= 0):
            self.set_console_text("MODBUS: %s, " %port + "No response from slave")
            return (self.MD_NO_RESPONSE, 0000)
        self.ser[port][0].flushInput()  
        return self.decode_modbus_reply(code, data, encodeline)       
                     
    def start_fct(self, hmi_port, scada_port, uart0_port, rate, uut, en_print):
        if (uut == "CCB"):
            if (en_print):
                print "CCB FCT start."
            import fct_ccb
            self.fct_ccb_running = 1
            self.modbus_log = en_print
            
            serial_number = self.EntryOfSerialNumber.get_text()
            if serial_number=="" or serial_number == "Please input serial number.":
                self.insert_into_console("Please scan barcode first, and click the start button again.\n")
                self.fct_ccb_running = 0
                self.EntryOfSerialNumber.grab_focus()     
                return 
            self.serial_number = serial_number
            self.insert_into_console("SN:"+self.serial_number+"\n")
        
            self.setup_serial(hmi_port, "38400")
            self.setup_serial(scada_port, "38400")
            self.setup_serial(uart0_port, "38400")      
            if self.ThreadOfFCTBatch == None or not self.ThreadOfFCTBatch.is_alive():
                self.ThreadOfFCTBatch = Thread(target=fct_ccb.FCTCCB, args=(self, hmi_port, scada_port, uart0_port, en_print))
                self.ThreadOfFCTBatch.start()
                time.sleep(0.8)
                self.ThreadOfFCTBatch.join(2) 
            #fct_ccb.FCTCCB(self, hmi_port, scada_port, uart0_port, en_print).run()
            
        else:
            print "UUT was not supported now."
        
    def GPIO_init(self):               
        # CCB firmware set the slave id to 1 for 3 kinds of MODBUS ports.
        self.slave_id = 1
                
        #==========RaspberryPi Pins=========#     
        # GPIO-Pins for SPI application BCM mode
        #self.SCLK        = 11 # Serial-Clock
        #self.MOSI        = 10 # Master-Out-Slave-In
        #self.MISO        = 9 # Master-In-Slave-Out
        #self.CS          = 8 # Chip-Select  
        #self.CE1        = 7
        #self.LATCH1     = 17
        #self.LATCH2     = 18
        #self.LATCH3     = 27
        #self.LATCH4     = 22
        #self.FAULT      = 23
        #self.CLEAR      = 24
        
        # GPIO-Pins for SPI application Board Mode
        self.SCLK        = 23 # Serial-Clock
        self.MOSI        = 19 # Master-Out-Slave-In
        self.MISO        = 21 # Master-In-Slave-Out
        self.CS          = 24 # Chip-Select  
        self.CE1        = 26
        self.LATCH1     = 11
        self.LATCH2     = 12
        self.LATCH3     = 13
        self.LATCH4     = 15
        self.FAULT      = 16
        self.CLEAR      = 18
            
        if os.name == 'posix' :                  
            #GPIO.setmode(GPIO.BCM)
            GPIO.setmode(GPIO.BOARD)
            GPIO.setwarnings(False)
            
            # Pin-Programming
            GPIO.setup(self.SCLK, GPIO.OUT)
            GPIO.setup(self.MOSI, GPIO.OUT)
            GPIO.setup(self.MISO, GPIO.IN)
            GPIO.setup(self.CS,   GPIO.OUT)
            
            GPIO.setup(self.CE1,    GPIO.OUT)
            GPIO.setup(self.LATCH1, GPIO.OUT)
            GPIO.setup(self.LATCH2, GPIO.OUT)
            GPIO.setup(self.LATCH3, GPIO.OUT)
            GPIO.setup(self.LATCH4, GPIO.OUT)
            GPIO.setup(self.CLEAR,     GPIO.OUT)
            
            # Prepare
            GPIO.output(self.CS,        GPIO.HIGH)
            GPIO.output(self.CE1,       GPIO.HIGH)    
            GPIO.output(self.SCLK,      GPIO.LOW)  
            GPIO.output(self.LATCH1,    GPIO.HIGH)   
            GPIO.output(self.LATCH2,    GPIO.HIGH)   
            GPIO.output(self.LATCH3,    GPIO.HIGH)   
            GPIO.output(self.LATCH4,    GPIO.HIGH)  
            GPIO.output(self.CLEAR,     GPIO.HIGH)
            GPIO.output(self.CLEAR,     GPIO.LOW)
        
    def MCP_init(self):      
        #==========MCP23S17 SPI=========#     
        # MCP23S17 chip select  
        self.SPI_U6_CS = 0       
        self.SPI_U7_CS = 1      
        self.SPI_U8_CS = 2         
        self.SPI_U9_CS = 3      
               
        # MCP23S17 register
        self.SPI_IODIRA = 0
        self.SPI_IODIRB = 1
        self.SPI_IPOLA = 2
        self.SPI_IPOLB = 3
        self.SPI_GPINTENA = 4
        self.SPI_GPINTENB = 5
        self.SPI_DEFVALA = 6
        self.SPI_DEFVALB = 7
        self.SPI_INTCONA = 8
        self.SPI_INTCONB = 9
        self.SPI_IOCONA = 10
        self.SPI_IOCONB = 11
        self.SPI_GPPUA = 12
        self.SPI_GPPUB = 13
        self.SPI_INTFA = 14
        self.SPI_INTFB = 15
        self.SPI_INTCAPA = 16
        self.SPI_INTCAPB = 17
        self.SPI_GPIOA = 18
        self.SPI_GPIOB = 19
        self.SPI_OLATA = 20
        self.SPI_OLATB = 21  
           
        self.SPI_SLAVE_ADDR  = 0x40
        
        self.SPI_SLAVE_WRITE = 0x00
        self.SPI_SLAVE_READ  = 0x01
   
        if os.name == 'posix' :
            # Enable cs address  
            #for i in range(0,7):
                #self.mcp_spi_write((self.SPI_SLAVE_ADDR + i*2), self.SPI_IOCONA, 0x08) 
            self.mcp_spi_write(0x40, self.SPI_IOCONA, 0x08)    
            self.mcp_spi_write(0x42, self.SPI_IOCONA, 0x08)    
            self.mcp_spi_write(0x44, self.SPI_IOCONA, 0x08)    
            self.mcp_spi_write(0x46, self.SPI_IOCONA, 0x08)    
            self.mcp_spi_write(0x48, self.SPI_IOCONA, 0x08)    
            self.mcp_spi_write(0x4a, self.SPI_IOCONA, 0x08)    
            self.mcp_spi_write(0x4c, self.SPI_IOCONA, 0x08)    
            self.mcp_spi_write(0x4e, self.SPI_IOCONA, 0x08)
        
    def DAC_init(self):
        #==========DAC SPI=========#           
        self.daclatch = [self.LATCH1, self.LATCH2, self.LATCH3, self.LATCH4] 
        self.dac_start_id = 4      
          
        # higher 8-bits input shift register, Address byte functions
        self.DAC_ADDR_NOP       = 0x00
        self.DAC_ADDR_DATA      = 0x01
        self.DAC_ADDR_READBACK  = 0x02
        self.DAC_ADDR_CONTROL   = 0x55
        self.DAC_ADDR_RESET     = 0x56
        
        # lower 16-bits input shift register:
        # 1 NOP
        # 2 Data
        # 3 Readback
        self.DAC_READBACK_STATUS    = 0x00
        self.DAC_READBACK_DATA      = 0x01
        self.DAC_READBACK_CONTROL   = 0x02
        # 4 Control register
        self.DAC_CTRL_REXT      = (1<<13)
        self.DAC_CTRL_OUTEN     = (1<<12)
        self.DAC_CTRL_SREN      = (1<<4)
        self.DAC_CTRL_DCEN      = (1<<3)                                 
        self.DAC_CTRL_420MA     = 0x05
        self.DAC_CTRL_020MA     = 0x06
        self.DAC_CTRL_024MA     = 0x07
        # 5 Reset register
        self.DAC_RESET          = 0x01                               
        
        if os.name == 'posix' :
            self.dac_spi_write(4, self.DAC_ADDR_CONTROL, self.DAC_CTRL_OUTEN|self.DAC_CTRL_024MA)
            self.dac_spi_write(5, self.DAC_ADDR_CONTROL, self.DAC_CTRL_OUTEN|self.DAC_CTRL_024MA)
            self.dac_spi_write(6, self.DAC_ADDR_CONTROL, self.DAC_CTRL_OUTEN|self.DAC_CTRL_024MA)
            self.dac_spi_write(7, self.DAC_ADDR_CONTROL, self.DAC_CTRL_OUTEN|self.DAC_CTRL_024MA)
        
    def MODBUS_init(self):        
        #==========MODBUS communication=========#     
        # MODBUS function code
        self.MB_CODE_READ           = 3
        self.MB_CODE_SINGLE_WRITE   = 6
        self.MB_CODE_DIAGNOSTIC     = 8 
        self.MB_CODE_MULTI_WRITE    = 16 
        self.MB_SUBCODE_QUERY       = 0
        
        self.MD_OK            = 0x0000
        self.MD_NO_RESPONSE   = 0x0001
        self.MD_EXCEPTION     = 0x0002
        self.MD_UNEXPECTED    = 0x0003
        
        self.MB_RESEND_TIMES = 30
        self.MB_TIMEOUT_TIMES = 6
        
        # Table of CRC values for the high-order byte
        self.auchCRCHi = (
            0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
            0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
            0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
            0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
            0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
            0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
            0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
            0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
            0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
            0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
            0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
            0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
            0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
            0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
            0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
            0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
            )
        
        # Table of CRC values for the low-order byte
        self.auchCRCLo =(
            0x00, 0xC0, 0xC1, 0x01, 0xC3, 0x03, 0x02, 0xC2, 0xC6, 0x06, 0x07, 0xC7, 0x05, 0xC5, 0xC4, 0x04,
            0xCC, 0x0C, 0x0D, 0xCD, 0x0F, 0xCF, 0xCE, 0x0E, 0x0A, 0xCA, 0xCB, 0x0B, 0XC9, 0x09, 0x08, 0xC8,
            0xD8, 0x18, 0x19, 0xD9, 0x1B, 0xDB, 0xDA, 0x1A, 0x1E, 0xDE, 0xDF, 0x1F, 0xDD, 0x1D, 0x1C, 0xDC,
            0x14, 0xD4, 0xD5, 0x15, 0xD7, 0x17, 0x16, 0xD6, 0xD2, 0x12, 0x13, 0xD3, 0x11, 0xD1, 0xD0, 0x10,
            0xF0, 0x30, 0x31, 0xF1, 0x33, 0xF3, 0xF2, 0x32, 0x36, 0xF6, 0xF7, 0x37, 0xF5, 0x35, 0x34, 0xF4,
            0x3C, 0xFC, 0xFD, 0x3D, 0xFF, 0x3F, 0x3E, 0xFE, 0xFA, 0x3A, 0x3B, 0xFB, 0x39, 0xF9, 0xF8, 0x38,
            0x28, 0xE8, 0xE9, 0x29, 0xEB, 0x2B, 0x2A, 0xEA, 0xEE, 0x2E, 0x2F, 0xEF, 0x2D, 0xED, 0xEC, 0x2C,
            0xE4, 0x24, 0x25, 0xE5, 0x27, 0xE7, 0xE6, 0x26, 0x22, 0xE2, 0xE3, 0x23, 0xE1, 0x21, 0x20, 0xE0,
            0xA0, 0x60, 0x61, 0xA1, 0x63, 0xA3, 0xA2, 0x62, 0x66, 0xA6, 0xA7, 0x67, 0xA5, 0x65, 0x64, 0xA4,
            0x6C, 0xAC, 0xAD, 0x6D, 0xAF, 0x6F, 0x6E, 0xAE, 0xAA, 0x6A, 0x6B, 0xAB, 0x69, 0xA9, 0xA8, 0x68,
            0x78, 0xB8, 0xB9, 0x79, 0xBB, 0x7B, 0x7A, 0xBA, 0xBE, 0x7E, 0x7F, 0xBF, 0x7D, 0xBD, 0xBC, 0x7C,
            0xB4, 0x74, 0x75, 0xB5, 0x77, 0xB7, 0xB6, 0x76, 0x72, 0xB2, 0xB3, 0x73, 0xB1, 0x71, 0x70, 0xB0,
            0x50, 0x90, 0x91, 0x51, 0x93, 0x53, 0x52, 0x92, 0x96, 0x56, 0x57, 0x97, 0x55, 0x95, 0x94, 0x54,
            0x9C, 0x5C, 0x5D, 0x9D, 0x5F, 0x9F, 0x9E, 0x5E, 0x5A, 0x9A, 0x9B, 0x5B, 0x99, 0x59, 0x58, 0x98,
            0x88, 0x48, 0x49, 0x89, 0x4B, 0x8B, 0x8A, 0x4A, 0x4E, 0x8E, 0x8F, 0x4F, 0x8D, 0x4D, 0x4C, 0x8C,
            0x44, 0x84, 0x85, 0x45, 0x87, 0x47, 0x46, 0x86, 0x82, 0x42, 0x43, 0x83, 0x41, 0x81, 0x80, 0x40,
            )
                    
    def __init__(self):
        import sys
        self.running_mode = 'calibration'
        if len(sys.argv) > 1:
            self.running_mode = sys.argv[1]
        
        builder = gtk.Builder()
        builder.add_from_file("./glades/calibration.glade")
        builder.connect_signals(self)
        
        self.ButtonResultByColor = builder.get_object("ButtonResultByColor")
        self.ButtonYes = builder.get_object("ButtonYes")
        self.ButtonNo = builder.get_object("ButtonNo")
        self.ButtonYes1 = builder.get_object("ButtonYes1")
        self.ButtonNo1 = builder.get_object("ButtonNo1")
        self.ButtonPrinting = builder.get_object("ButtonPrinting")
        self.ButtonYes.child.modify_font(pango.FontDescription("sans 48"))
        self.ButtonNo.child.modify_font(pango.FontDescription("sans 48"))
        self.ButtonYes1.child.modify_font(pango.FontDescription("sans 48"))
        self.ButtonNo1.child.modify_font(pango.FontDescription("sans 48"))
        self.LabelOfInstruction = builder.get_object("LabelOfInstruction")
        self.LabelOfInstruction.modify_font(pango.FontDescription("sans 30"))
    
        self.ListStoreOfUart = builder.get_object("liststore2")
        self.ComboBoxOfUart = builder.get_object("ComboBoxOfUart")
        self.window = builder.get_object("window")
        
    
        self.TextBufferOfLog = builder.get_object("textbuffer1")
        self.EntryOfCommand = builder.get_object("EntryOfCommand")
        self.EntryOfSerialNumber = builder.get_object("EntryOfSerialNumber")
        self.serial_number = 777
        self.sn_len = 11
        self.ScrolledWindowOfLog = builder.get_object("ScrolledWindowOfLog")
        self.FileChooserButton = builder.get_object("FileChooserButton")
        self.FileChooserButtonOfTestMode = builder.get_object("FileChooserButtonOfTestMode")
        self.FileFilterForView = builder.get_object("filefilter1")
        self.FileFilterForView.add_pattern("*.cali")
        self.FileFilterForView.add_pattern("*.bas")
        self.tutorial_frame = builder.get_object('frame3')
        #self.tutorial_frame.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("blue"))

        if self.running_mode == 'serial':
            passfail_hbox = builder.get_object('HboxOfPassFail')
            debug_frame = builder.get_object('FrameOfDebug')
            status_hbox = builder.get_object('hbox5')
            self.tutorial_frame.set_visible(0)
            passfail_hbox.set_visible(0)
            debug_frame.set_visible(1)
            status_hbox.set_visible(0)
        elif self.running_mode == 'debug':
            print "(debug mode)"
            import faulthandler
            faulthandler.enable()
            
        try: 
            default_script = './scripts/ntc.bas'
            with open("./cali.conf") as file:
                for line in file:
                    val_list = line.split("=") 
                    if val_list[0] == "DEFAULT_SCRIPT":
                        default_script = val_list[1].rstrip()
                        break
        except:
            print "cali.conf open failed."
        if os.path.isfile(default_script):
            self.FileChooserButtonOfTestMode.set_filename(default_script)
            self.FileChooserButtonOfTestMode.set_filename(default_script)
        self.ImageOfTutorial = builder.get_object("ImageOfTutorial") 
        self.FrameOfDebug = builder.get_object("FrameOfDebug")
        self.HboxOfPassFail = builder.get_object("HboxOfPassFail")
        self.ListOfPrinterSettings = [None]
        # init for multiple threading        
        self.ply_need_start = 0
        self.ply_mode = 0   # 0: line by line 1: yacc mode
        self.ack_to_plying = 1  # 0 ack 1 not ack
        self.batch_is_timeout = 0
        self.check_status = 0   # 1: failed 
                                # 0: success 
                                # 0x8000000x: terminated
        self.led_check_status = 0
        self.fct_ccb_running = 1      
        self.ThreadOfSerialReceiving = None  
        self.ThreadOfPly = None 
        self.ThreadOfBatch = None
        self.ThreadOfFCTBatch = None
        self.batching_result = {}
        self.mutex = threading.Lock()
        self.mutex_of_plyack = threading.Lock()
        #self.mutex_of_ply = threading.Lock() 
        self.condition = threading.Condition(threading.Lock())
        self.modbus_log = 0
        
        self.ComboxOfUart_init() 
        #self.USB_init()
              
        self.GPIO_init()  
        self.MCP_init()
        self.DAC_init()
        self.MODBUS_init()
       
        self.window.show_all()

    def main(self):
        gobject.threads_init()
        gtk.gdk.threads_init()  # use GIL to switch the multi-threads
        
        # NEVER directly operate GTK related resources but use
        # 1) put threads_enter()/leave() to wrap gtk.main() and other gtk_operations in your threads. 
        # 2) use gobject.idle_add(function_of_gtk_operation, counter) in your threads. (Recommended) 
        gtk.threads_enter()      
        gtk.main()               
        gtk.threads_leave()
        
if __name__ == "__main__":
    cali = CaliTest()
    cali.main()
    
