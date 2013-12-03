baterm.py - Beyond the traditional Terminal program.
=========

A standard UART terminal with built-in BASIC interpretor engine.


For a quick overview of the code, please start from cali_test.py

Before running the program, you need to install several python package by below command. I assume you are using Windows here.


1. Get the pygtk by installing pygtk all-in-one package (e.g. pygtk-all-in-one-2.24.0.win32-py2.7.msi) from http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/ 

2. Get easy_install by downloading setuptools-1.4.2.tar.gz from https://pypi.python.org/pypi/setuptools#downloads

   Extract setuptools-1.4.2.tar.gz and run: 

	 python setup.py install

   Then add "C:\Python27\Scripts" to $PATH

3. Get the pyserial by

	 easy_install pyserial

4. Get ply by

	 easy_install ply
	 
5. Get chardet

	 easy_install chardet
