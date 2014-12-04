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
import chardet

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
        print "leaving..."
  
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
        if self.auto_scroll:
            adj = self.ScrolledWindowOfLog.get_vadjustment()
            #adj.set_value(adj.upper - adj.page_size)
            gobject.idle_add(adj.set_value, (adj.upper - adj.page_size))
    
    def on_TextViewOfLog_scroll_event(self, widget, event):
        adj = self.ScrolledWindowOfLog.get_vadjustment()
        print adj.value, adj.upper-adj.page_size
        if abs(adj.value-(adj.upper-adj.page_size)) < 0.1:
            self.auto_scroll = True
        else:
            self.auto_scroll = False
        
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
            if cmd[0].startswith('_'):  # local and mcu's command
                cmd[0] = cmd[0].lower()
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
                            if self.ThreadOfReceiving == None or not self.ThreadOfReceiving.is_alive():
                                # Entering BASIC standalone mode
                                #self.insert_into_console("Please check the UART connection and restart the program.\n")
                                self.insert_into_console("PLY processing with file " + cmd[1] + "\n")
                                self.cmds = cmd[1]
                                self.ply_mode = 1
                                if self.ThreadOfPly == None or not self.ThreadOfPly.is_alive():
                                    self.ThreadOfPly = Thread(target=self.plying, args=(0, self.ply_mode,))
                                    self.ThreadOfPly.start()
                                    time.sleep(0.1)
                                    self.ThreadOfPly.join()
                                #self.set_check_status(1)
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
                    ###gtk.threads_enter()
                    self.insert_into_console("\nPlease connect the serial device and reboot the program.\n")
                    ###gtk.threads_leave()
                else:
                    if left > 0 :
                        line += self.ser[port][0].read(left)   
                        if line != '' :
                            ###gtk.threads_enter()
                            line = line.decode(chardet.detect(line)['encoding'])
                            self.insert_into_console(line)
                            ###gtk.threads_leave()
                        line = ''
                
            else:
                print "thread receiving exit.."
                break
                #todo: need usb plug/unplug signal
            
            time.sleep(0.01)    # avoid too much cpu resource cost
            
    def get_batching_result(self, keywords):
        print 'key', keywords
        print "val", self.batching_result
        #keywords = keywords.upper()
        result = "None"
        if keywords in self.batching_result:
            result = self.batching_result[keywords]
            #del self.batching_result[keywords]    #may cause glibc "double free" bug.
            self.batching_result[keywords] = "None"
            if len(result) > 1:
                # convert it to num list
                numlist = []
                for num in result:
                    if num.isdigit():
                        numlist.append(num)
                result = numlist
                print "val list: " 
                print result
            else:
                result = result.strip() #remove leading/ending spaces
                regular = re.compile(r'[-+]?[0-9]+\.?[0-9]*$')   # match numbers
                if regular.match(result) != None:
                    result = float(result)
        return result
    
    def set_batching_result(self, result, rtype = "STRING"):
        print "set, ", result
        if len(result) > 1:
            if rtype == "STRING":
                self.batching_result[result[0]] = result[1]
            elif rtype == "ARRAY":
                self.batching_result[result[0]] = result[1:len(result)]
        
    def batching(self, port, cmd, check_mode):
        #print "thread batching starts...\n"

        self.ser[port][0].flushInput()
        self.ser[port][0].flushOutput()
        
        #for cmd in self.cmds:
        cmd = cmd.strip()
        self.ser[port][0].write(cmd + "\n")
        #if check_mode == "AUTO":
        if check_mode.startswith("AUTO"):
            while True:
                ch = self.ser[port][0].read(1)                
                if ch.isdigit() or self.batch_is_timeout == 1:
                    break
        #time.sleep(0.5)
        if check_mode == "MANUAL":
            time.sleep(0.5) # no wait when "NOCHECK"
            ch = self.ser[port][0].read(1)
        text = ''
        line = cmd + " "
        #if check_mode == "AUTO":
        if check_mode.startswith("AUTO"):
            if self.batch_is_timeout == 1:
                self.batch_is_timeout = 0
                #ch = '1'
                text = "(timeout)"
            
            #self.ser[port][0].flushInput()
            if check_mode == "AUTO":
                if ch == '0':
                    self.set_check_status(0)
                    text += " is succeed"
                else:
                    self.set_check_status(1)
                    text += " is failed" 
            text += '(' + ch + ')'  
            self.ack_to_plying = 0   
            #gtk.threads_enter()
            self.insert_into_console(cmd + text)
            #gtk.threads_leave()            
            #line = line + ch + ' '  
        if check_mode == "NOCHECK":
            self.set_check_status(0)
            self.ack_to_plying = 0
        else:
            left = self.ser[port][0].inWaiting()
            if left > 0:
                line += self.ser[port][0].read(left)   
                #if check_mode != "AUTO":
                self.insert_into_console('\n Read from slave:' + line)
                self.set_batching_result(line.split())
        self.ser[port][0].flushInput()
        #print "thread batching stopped.\n"

    def plying(self, port=0, method=0):   # 0: line by line 1: Lex-Yacc method    

        print "thread plying starts.."
        self.clear_status()  
        self.timer_event()     
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
        if cmd == None or cmd == "":
            return
        if cmd.startswith('_'):
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
                self.serial_number = (self.EntryOfSerialNumber.get_text()).strip()
                #if not self.serial_number.isdigit():
                if len(self.serial_number) < 1:
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
                        uart_conn_result = self.set_uart_text(port, baudrate, check, None, parity)
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
            elif cmd == '_TESTARRAY':   
                replied_oct_digit = '01 02 03 04 05'
                data_with_multiline = ('_TESTARRAY ' + replied_oct_digit).split()
                self.set_batching_result(data_with_multiline, "ARRAY")
            elif cmd == '_TESTARRAY2':   
                replied_hex_str = '11 12 13 a4 a5'
                data_with_multiline = replied_hex_str.split()
                data_with_multiline_oct = [str(int(x, 16)) for x in data_with_multiline]
                data_with_multiline = ['_TESTARRAY2'] + data_with_multiline_oct    
                #data_with_multiline = ('_TESTARRAY2 ' + '11 12 13 a4 a5').split()
                self.set_batching_result(data_with_multiline, "ARRAY")
                 
        else:   # end startswith "_"
            # check if it is a uart port
            cmdlist = cmd.split()
            if len(cmdlist) > 1:
                port = cmdlist[0]
                command = cmdlist[1]
                if port in self.ser:
                    baudrate = self.ser[port][1]
                    uart_conn_result = self.set_uart_text(port, baudrate, str(command))
                    return
        
            #otherwise, just print it on the Console window
            cmd = cmd.decode(chardet.detect(cmd)['encoding'])  # decode() means decode the wanted format to unicode format.
            self.insert_into_console(cmd)
        ###gtk.threads_leave()
    
    def insert_into_console(self, cmd=None):
        if cmd != None:
            gobject.idle_add(self.TextBufferOfLog.insert_at_cursor, cmd)
            
    def set_uart_text(self, port, rates, check_mode="AUTO", cmd=None, parity='N'):
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
        
#        if check_mode == "AUTO": # auto check
        if cmd != None: # in case a new uart connection request without command transferring.
            for i in range(1,3):
                if self.ThreadOfBatch == None or not self.ThreadOfBatch.is_alive():
                    print "batching times:", i
                    self.ThreadOfBatch = Thread(target=self.batching, args=(port, cmd, check_mode))
                    self.ThreadOfBatch.start()
                    time.sleep(0.1)
                    self.ThreadOfBatch.join(2) 
                    if self.ThreadOfBatch.is_alive():
                        self.batch_is_timeout = 1
                        time.sleep(2)
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
        font_size = 24
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
    
    def flash_msp430(self, hexfile):
        cmds = ['-eE', '-PV', '-r', '-i', 'ihex', hexfile]
        jtagfile = './msp430-jtag.py'
        if not os.path.isfile(jtagfile):
            jtagfile = './msp430-jtag.pyc'
        self.cmds = ['python', jtagfile, '--time', '-p']
        if os.name == 'posix':
            os.environ['LIBMSPGCC_PATH'] = '/usr/lib'
            self.cmds.append('/dev/ttyACM0')
        else:
            self.cmds.append('TIUSB')
            
        self.cmds += cmds
        
        if os.name == 'posix':
            command = ''
            for cmd in self.cmds:
                command += cmd
                command += ' '
            start_time = time.time()
            import pexpect
            child = pexpect.spawn(command)
            result = ''
            while True:
                try:       
                    child.expect('\r')
                    result += child.before
                    #gtk.threads_enter()                    
                    self.insert_into_console(child.before)
                    #gtk.threads_leave()
                except:
                    #gtk.threads_enter()
                    self.insert_into_console("\nTime: " + str(time.time() - start_time) + 's\n')
                    #gtk.threads_leave()
                    break
                time.sleep(0.1)
            
        else:    
            import subprocess    
            proc = subprocess.Popen(self.cmds, 
                            shell=False, 
                            stderr=subprocess.PIPE)
            ###gtk.threads_enter()
            result = proc.communicate()[1]
            self.insert_into_console(result)
            ###gtk.threads_leave()

        if ('Erase check by file: OK' or 'Programming: OK' or 'Verify by file: OK') not in result:
            #gtk.threads_enter()
            self.insert_into_console("flash failed.\n")
            ###gtk.threads_leave()
            self.set_check_status(1)

        
    def ComboxOfUart_init(self):
        self.ser = {}   #{reference, instance, is_alive}
        ports = sorted(comports())
        
        while self.ComboBoxOfUart.get_active() != -1:
            self.ComboBoxOfUart.remove_text(self.ComboBoxOfUart.get_active())
        
        port_num = 0
        for port, desc, hwid in ports:
            if port.find('ttyACM') == -1:
                if self.running_mode == 'serial':
                    self.ListStoreOfUart.append([port, '115200'])
                self.ListStoreOfUart.append([port, '9600'])
                self.ser[port] = None, 0          
                port_num += 1 
                
        if port_num == 0 :
            self.ComboBoxOfUart.insert_text(0, "NONE")
            
        self.ComboBoxOfUart.set_active(0)
        
    def serial_connect(self, port, rates, parity="N"):
        try: 
            self.ser[port] = serial.Serial(port, rates, parity=parity, timeout=1), rates
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
        import sys
        self.running_mode = 'serial'
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
        self.ListStoreOfUart = builder.get_object("liststore2")
        self.ComboBoxOfUart = builder.get_object("ComboBoxOfUart")
        self.window = builder.get_object("window")
        
        self.TextBufferOfLog = builder.get_object("textbuffer1")
        self.auto_scroll = True
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
        self.ThreadOfReceiving = None    
        self.ThreadOfPly = None 
        self.ThreadOfBatch = None
        self.batching_result = {}
        self.mutex = threading.Lock()
        self.mutex_of_plyack = threading.Lock()
        #self.mutex_of_ply = threading.Lock() 
        self.condition = threading.Condition(threading.Lock())
        self.ComboxOfUart_init()
        
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
    
