#!/usr/bin/env python

import printer
import gtk

class CaliScan():
    def on_WindowOfScanning_expose_event(self, widget, data=None):
        #if self.EntryOfTester.get_text().rstrip() == "":
        #    self.EntryOfTester.set_text("Hach")
        if self.EntryOfSNLen.get_text().rstrip() == "":
            self.EntryOfSNLen.set_text(str(self.sn_len))
            
    def on_WindowOfScanning_key_press_event(self, widget, event):
        key = gtk.gdk.keyval_name(event.keyval)
        if key == "Return":
            self.on_ButtonPrinting_clicked(0, None)      
                  
    def on_ComboBoxOfScan_changed(self, widget, data=None):
        print self.ComboBoxOfScan.get_active_text()

    def on_ButtonPrinting_clicked(self, widget, data=None):
        sn = self.EntryOfSN.get_text().rstrip()
        tester = self.EntryOfTester.get_text().rstrip()
        sn_len = self.EntryOfSNLen.get_text().rstrip()
        if not sn_len.isdigit():
            sn_len = 10
        if len(sn) == int(sn_len):  # and tester != "":
            self.ListOfPrinterSettings[0] = printer.GtkPrinter(self.ListOfPrinterSettings[0], tester, sn, self.console_log, self.cert_format).run(mode="print")
            self.window.destroy()
        else:
            self.EntryOfSN.set_text("S/N length wrong.")
            self.EntryOfSN.grab_focus()
            
    def on_ButtonPrinter_clicked(self, widget, data=None):
        self.ListOfPrinterSettings[0] = printer.GtkPrinter(self.ListOfPrinterSettings[0], None, None, None, None).run(mode="setup")

    def run(self, parent_window):
        self.window.set_transient_for(parent_window)   # will make the child window located at center of main window. why??
        self.window.show_all()
        
    def __init__(self, printer_settings_mutable, console_log, cert_format="EC", sn_len=10):

        self.ListOfPrinterSettings = printer_settings_mutable   # mutable means: 1. to pass a var by reference, use list type var.
                                                                #                2. otherwise, directly pass a var will only pass its copy
        self.console_log = console_log
        
        if cert_format != "EC" and cert_format != "PH":
            cert_format = "EC"
        self.cert_format = cert_format
        self.sn_len = sn_len
        
        builder = gtk.Builder()
        builder.add_from_file("./glades/scanwindow.glade")
        builder.connect_signals(self)
        self.window = builder.get_object("WindowOfScanning")
        self.EntryOfSN = builder.get_object("EntryOfSN")
        self.EntryOfTester = builder.get_object("EntryOfTester")      
        self.EntryOfSNLen = builder.get_object("EntryOfSNLen")  
        