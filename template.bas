1 REM :: 
2 REM :: 
3 REM :: BASIC COMMAND LIST.
4 REM ::       	GUI 	:	WILL SEND THE COMMAND IN "" TO THE GUI INTERFACE. 
5 REM ::       					GUI "_clear", WILL CLEAR THE GUI CONSOLE
6 REM ::       					GUI "_stop", WILL STOP THE CALIBRATION PROCESS
7 REM ::       	LET		:	USED TO ASSIGN NUMBERS 
8 REM ::						LET I = 0.1, WILL ASSIGN 0.1 TO VARIABLE I	
9 REM ::		LETSTR	: 	USED TO ASSIGN STRINGS
10 REM ::				 		LETSTR MCUPORT = "COM3" ,WILL ASSIGN "COM3" TO MCUPORT
11 REM ::		OUT		:	WILL OUTPUT STRINGS TO THE DESTINATION PORT
12 REM ::				 	(1) BEFORE USE OUT COMMAND, YOU NEED TO ASSIGN THE OUTPUT PORT FIRST
13 REM ::				 		LETSTR MCUPORT = "COM3"
14 REM ::				 		LETSTR DEVICEPORT = "COM4"
15 REM ::						LETSTR CONSOLE = "CONSOLEs"	
16 REM ::				 	(2) THEN, 
17 REM ::				 		OUT MCUPORT = "CMD", WILL OUTPUT CMD IN "" TO THE MCU UART PORT (COM3)
18 REM ::				 		OUT DEVICEPORT = "CMD" WILL OUTPUT CMD IN "" TO THE DEVICE PORT (COM4)
19 REM :: 				 		OUT CONSOLE = "Hello", WILL OUTPUT STRING HELLO IN "" TO GUI CONSOLE.
20 REM ::		CHECK	: 	WILL CHECK OUT THE RESULT BACK FROM UART
21 REM ::				 		CHECK "AUTO", WILL CHECK THE RESULT AUTOMATICALLY
22 REM ::				 		CHECK "MANUAL", WILL CHECK THE RESULT BY HUMAN
23 REM ::		DELAY	: 	WILL DELAY ASSIGNED TIME INTERVAL
24 REM ::						DELAY 1, WILL DELAY 1s
25 REM :: 						DELAY 0.1, WILL DELAY 100ms
26 REM ::						DELAY 0, Will PAUSE AND WAIT HUMAN'S INPUT
27 REM ::
28 REM ::
29 REM :: ADVANCED COMMAND LIST.
30 REM :: 		PLEASE REFER TO BELOW TABLE AND FIND OUT THE DEFINITIONS IN BASIC PROGRAMMING BOOKS
31 REM ::    		'LET','READ','DATA','PRINT','GOTO','IF','THEN','FOR','NEXT','TO','STEP',
32 REM ::		    'END','STOP','DEF','GOSUB','DIM','REM','RETURN','RUN','LIST','NEW',

40 CLEAR "CONSOLE"

50 REM ======== DO NOT CHANGE BELOW VARIABLE NAME ========
51 LETSTR TUTORIAL = "TUTORIALs"
52 LETSTR CONSOLE = "CONSOLEs"
53 LETSTR MCUPORT = "COM3"
55 LET MCUBAUD = 115200
56 LETSTR DEVICEPORT = "COM14"
57 LET DEVICEBAUD = 9600
60 REM ======== DO NOT CHANGE ABOVE VARIABLE NAME ========

63 OUT TUTORIAL = "12082bb.bmp"
64 OUT CONSOLE = "��SEE THE PICUTRE? Hit �س�  if yes"
65 DELAY 0
66 REM CHECK "MANUAL"
67 REM OUT CONSOLE = "Please check the pwd command"
68 REM OUT MCUPORT = "pwd"
71 FOR I = 1 TO 4
72 OUT CONSOLE = I
73 REM CHECK "MANUAL"
74 OUT CONSOLE = "Please Check SB function."
75 OUT DEVICEPORT = "SB"
76 REM IF I = 5 THEN 92
77 CHECK "AUTO"
78 OUT CONSOLE = "Check ID function automatically."
79 OUT DEVICEPORT = "ID"
90 NEXT I
91 OUT TUTORIAL = "120826P-007.JPG"
100 REM GUI "_stop"
110 OUT CONSOLE = "Stopped."
200 END
