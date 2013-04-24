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
50 REM ======== DO NOT CHANGE BELOW VARIABLE NAME ========
51 LETSTR CONSOLE = "CONSOLEs"
52 LETSTR INSTRUCTION = "INSTRUCTIONs"
53 LETSTR FLASH = "FLASHs"
54 LETSTR TUTORIAL = "TUTORIALs"
55 LET MCUBAUD = 9600
56 LET DEVICEBAUD = 9600
60 REM ======== DO NOT CHANGE ABOVE VARIABLE NAME ========

69 OUT INSTRUCTION = "设定治具板通讯端口", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
70 LET ERRPOS = 0
71 OUT CONSOLE = "_CLEAR"
72 OUT TUTORIAL = "DanaherLogo.JPG"
74 OUT CONSOLE = "_CURRENTTIME"
75 LETSTR COMMERRORSTR = " "

80 CHECK "AUTODEBUG"
81 LETSTR MCUPORT = "/dev/ttyUSB0"
82 OUT MCUPORT = "ID"
83 READDATA IDUSB0 = "ID"

84 LETSTR MCUPORT = "/dev/ttyUSB1"
85 OUT MCUPORT = "ID"
86 READDATA IDUSB1 = "ID"

87 LETSTR MCUPORT = "/dev/ttyUSB2"
88 OUT MCUPORT = "ID"
89 READDATA IDUSB2 = "ID"

90 LETSTR MCUPORT = "/dev/ttyUSB3"
91 OUT MCUPORT = "ID"
92 READDATA IDUSB3 = "ID"
111 LETSTR ECJIGIDSTR = "LAVIDA_EC_JIG"
121 IF ECJIGIDSTR = IDUSB0 THEN 130
122 IF ECJIGIDSTR = IDUSB1 THEN 132
123 IF ECJIGIDSTR = IDUSB2 THEN 134
124 IF ECJIGIDSTR = IDUSB3 THEN 136
125 OUT CONSOLE = "ECJIG IDSTR NOT FIND"
126 OUT CONSOLE = "DEVICEPORT NOT SET"
127 LETSTR COMMERRORSTR = "驱动板COM 口通讯错误"
128 OUT CONSOLE = "_ERROR"
129 GOTO 10000

130 LETSTR MCUPORT = "/dev/ttyUSB0"
131 GOTO 150
132 LETSTR MCUPORT = "/dev/ttyUSB1"
133 GOTO 150
134 LETSTR MCUPORT = "/dev/ttyUSB2"
135 GOTO 150
136 LETSTR MCUPORT = "/dev/ttyUSB3"
137 GOTO 150

150 OUT INSTRUCTION = "治具驱动板通讯ok", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
151 OUT CONSOLE = "MCUPORT:"
152 OUT CONSOLE = MCUPORT


160 OUT TUTORIAL = "PlugConnectorEC.JPG"
161 OUT INSTRUCTION = "步骤1：请将仪器插上电源，\nP3接口接上信号线，P8口接上\n串口通讯线, 就绪后点通过", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
162 OUT MCUPORT = "STAB:1"
163 DELAY 0
164 OUT MCUPORT = "STPB"
165 OUT INSTRUCTION = "设定待测主板通讯端口，请等待！", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"

169 CHECK "AUTODEBUG"
170 LETSTR DEVICEPORT = "/dev/ttyUSB0"
171 OUT DEVICEPORT = "ID"
172 READDATA IDUSB0 = "ID"

180 LETSTR DEVICEPORT = "/dev/ttyUSB1"
181 OUT DEVICEPORT = "ID"
182 READDATA IDUSB1 = "ID"

183 LETSTR DEVICEPORT = "/dev/ttyUSB2"
184 OUT DEVICEPORT = "ID"
185 READDATA IDUSB2 = "ID"

186 LETSTR DEVICEPORT = "/dev/ttyUSB3"
187 OUT DEVICEPORT = "ID"
188 READDATA IDUSB3 = "ID"

199 LETSTR ECIDSTR = "EC"
200 IF ECIDSTR = IDUSB0 THEN 210
201 IF ECIDSTR = IDUSB1 THEN 212
202 IF ECIDSTR = IDUSB2 THEN 214
203 IF ECIDSTR = IDUSB3 THEN 216
204 OUT CONSOLE = "ECID NOT FIND"
206 OUT CONSOLE = "DEVICEPORT NOT SET"
207 LETSTR COMMERRORSTR = "待测板COM 口通讯错误"
208 OUT CONSOLE = "_ERROR"
209 GOTO 10000

210 LETSTR DEVICEPORT = "/dev/ttyUSB0"
211 GOTO 220
212 LETSTR DEVICEPORT = "/dev/ttyUSB1"
213 GOTO 220
214 LETSTR DEVICEPORT = "/dev/ttyUSB2"
215 GOTO 220
216 LETSTR DEVICEPORT = "/dev/ttyUSB3"

220 OUT INSTRUCTION = "待测板通讯ok", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"



500 OUT INSTRUCTION = "治具驱动板通讯ok", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
501 OUT CONSOLE = "MCUPORT:"
502 OUT CONSOLE = MCUPORT


510 CHECK "AUTO"

602 OUT MCUPORT = "STPB"
603 OUT INSTRUCTION = "初始化, 请等待！", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
604 OUT TUTORIAL = "DanaherLogo.JPG"
605 REM ========power on=========================
606 OUT DEVICEPORT = "POWER:1"
607 DELAY 3
608 REM ========continuous mode=========================
609 OUT DEVICEPORT = "press.key:7"

700 FOR K = 1 TO 10000
701 OUT CONSOLE = K, "TIMES"
704 OUT CONSOLE = "_CURRENTTIME"

1500 REM ================================ TEST COND: 0.045 uS ==================================
1501 LETSTR MSG = "0.045[0.03-0.06]uS/cm"
1502 OUT INSTRUCTION = "步骤2：测试0.045[0.03-0.06] uS/cm", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
1503 OUT MCUPORT = "OHM:10000000"
1504 DELAY 5
1505 LET LOWLIMIT = 0.04
1506 LET HIGHLIMIT = 0.05
1507 GOSUB 3000

1599 REM =============================== TEST COND: 0.225 uS ===================================
1600 LETSTR MSG = "0.225[0.20-0.25]uS/cm"
1601 OUT INSTRUCTION = "步骤3：测试0.225[0.20-0.25] uS/cm", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
1602 OUT MCUPORT = "OHM:2000000"
1603 DELAY 5
1604 LET LOWLIMIT = 0.2
1605 LET HIGHLIMIT = 0.25
1607 GOSUB 3000

1699 REM =============================== TEST COND: 0.9 uS ====================================
1700 LETSTR MSG = "0.9[0.88-0.92]uS/cm"
1701 OUT INSTRUCTION = "步骤4：测试0.90[0.88-0.92] uS/cm", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
1702 OUT MCUPORT = "OHM:500000"
1703 DELAY 8
1704 LET LOWLIMIT = 0.88
1705 LET HIGHLIMIT = 0.92
1707 GOSUB 3000

1799 REM ================================ TEST COND: 2.25 uS ==================================
1800 LETSTR MSG = "2.25[2.23-2.27]uS/cm"
1801 OUT INSTRUCTION = "步骤5：测试2.25[2.23-2.27] uS/cm", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
1802 OUT MCUPORT = "OHM:200000"
1803 DELAY 8
1805 LET LOWLIMIT = 2.23
1806 LET HIGHLIMIT = 2.27
1808 GOSUB 3000

2009 REM ================================= TEST COND: 4.50 uS =================================
2010 LETSTR MSG = "4.5[4.48-4.52]uS/cm"
2012 OUT INSTRUCTION = "步骤6：测试4.50[4.48-4.52] uS/cm", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
2013 OUT MCUPORT = "OHM:100000"
2014 DELAY 10
2015 LET LOWLIMIT = 4.48
2016 LET HIGHLIMIT = 4.52
2018 GOSUB 3000

2019 REM ================================= TEST COND: 22.5 uS ================================
2020 LETSTR MSG = "22.5[22.3-22.7]uS/cm"
2022 OUT INSTRUCTION = "步骤7：测试22.5[22.3-22.7] uS/cm", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
2023 OUT MCUPORT = "OHM:20000"
2024 DELAY 10
2025 LET LOWLIMIT = 22.3
2026 LET HIGHLIMIT = 22.7
2028 GOSUB 3000

2029 REM ================================= TEST COND: 45.0 uS ================================
2030 LETSTR MSG = "45.0[44.8-45.2]uS/cm"
2032 OUT INSTRUCTION = "步骤8：测试45.0[44.8-45.2] uS/cm", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
2033 OUT MCUPORT = "OHM:10000"
2034 DELAY 10
2035 LET LOWLIMIT = 44.8
2036 LET HIGHLIMIT = 45.2
2038 GOSUB 3000

2039 REM ================================= TEST COND: 225 uS ===============================
2040 LETSTR MSG = "225[223-227]uS/cm"
2042 OUT INSTRUCTION = "步骤9：测试225[223-227] uS/cm", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
2043 OUT MCUPORT = "OHM:2000"
2044 DELAY 10
2045 LET LOWLIMIT = 223
2046 LET HIGHLIMIT = 227
2048 GOSUB 3000

2049 REM ================================= TEST COND: 450 uS ===============================
2050 LETSTR MSG = "450[448-452]uS/cm"
2052 OUT INSTRUCTION = "步骤10：测试450[448-452] uS/cm", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
2053 OUT MCUPORT = "OHM:1000"
2054 DELAY 10
2055 LET LOWLIMIT = 448
2056 LET HIGHLIMIT = 452
2058 GOSUB 3000

2060 REM ================================= TEST COND: 2.25 mS ===============================
2061 LETSTR MSG = "2.25[2.23-2.27]mS/cm"
2062 OUT INSTRUCTION = "步骤11：测试2.25[2.23-2.27] mS/cm", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
2063 OUT MCUPORT = "OHM:200"
2064 DELAY 15
2065 LET LOWLIMIT = 2230
2066 LET HIGHLIMIT = 2270
2068 GOSUB 3000

2070 REM ================================== TEST COND: 9.00 mS ==============================
2071 LETSTR MSG = "9.00[8.98-9.02]mS/cm"
2072 OUT INSTRUCTION = "步骤12：测试9.0[8.98-9.02] mS/cm", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
2073 OUT MCUPORT = "OHM:50"
2074 DELAY 35
2075 LET LOWLIMIT = 8980
2076 LET HIGHLIMIT = 9020
2078 GOSUB 3000

2080 REM ================================= TEST COND: 90.0 mS =================================
2081 LETSTR MSG = "90.0[89.8-90.2]mS/cm"
2082 OUT INSTRUCTION = "步骤13：测试90.0[89.8-90.2] mS/cm", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
2083 OUT MCUPORT = "OHM:5"
2084 DELAY 40
2085 LET LOWLIMIT = 89800
2086 LET HIGHLIMIT = 90200
2088 GOSUB 3000


2100 REM =============================== TEST TEMP: 3℃ =======================================
2101 LETSTR ERRMSG = "3℃测试不通过"
2102 OUT INSTRUCTION = "步骤14：测试3.0[2.7-3.2] ℃", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
2103 OUT MCUPORT = "NC:3"
2104 DELAY 3
2105 LETSTR CMDSTR = "?NTC.T"
2106 LET LOWLIMIT = 2.8
2107 LET HIGHLIMIT = 3.2
2109 GOSUB 4000

2180 REM =============================== TEST TEMP: 15℃ =====================================
2181 LETSTR ERRMSG = "15℃测试不通过"
2182 OUT INSTRUCTION = "步骤15：测试15.0[14.8-15.2] ℃", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
2183 OUT MCUPORT = "NC:15"
2184 DELAY 3
2185 LETSTR CMDSTR = "?NTC.T"
2186 LET LOWLIMIT = 14.8
2188 LET HIGHLIMIT = 15.2
2190 GOSUB 4000

2280 REM ============================== TEST TEMP: 25℃ =====================================
2281 LETSTR ERRMSG = "25℃测试不通过"
2282 OUT INSTRUCTION = "步骤16：测试25.0[24.8-25.2] ℃", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
2283 OUT MCUPORT = "NC:25"
2284 DELAY 3
2285 LETSTR CMDSTR = "?NTC.T"
2286 LET LOWLIMIT = 24.8
2288 LET HIGHLIMIT = 25.2
2290 GOSUB 4000

2380 REM ============================== TEST TEMP: 37℃ =====================================
2381 LETSTR ERRMSG = "37℃测试不通过"
2382 OUT INSTRUCTION = "步骤17：测试37.0[36.8-37.2] ℃", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
2383 OUT MCUPORT = "NC:37"
2384 DELAY 3
2385 LETSTR CMDSTR = "?NTC.T"
2386 LET LOWLIMIT = 36.8
2388 LET HIGHLIMIT = 37.2
2390 GOSUB 4000

2480 REM ============================= TEST TEMP: 95℃ ======================================
2481 LETSTR ERRMSG = "95℃测试不通过"
2482 OUT INSTRUCTION = "步骤18：测试95.0[94.7-95.3] ℃", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
2483 OUT MCUPORT = "NC:95"
2484 DELAY 3
2485 LETSTR CMDSTR = "?NTC.T"
2486 LET LOWLIMIT = 94.7
2488 LET HIGHLIMIT = 95.3
2490 GOSUB 4000

2500 OUT CONSOLE = "    "
2502 OUT MCUPORT = "RESET"

2599 OUT CONSOLE = "_CLEAR"
2600 NEXT K

2700 CHECK "MANUAL"
2701 LET ERRPOS = 1
2702 LETSTR ERRMSG = "步骤19测试不通过"
2703 OUT INSTRUCTION = "步骤19，请拔除仪器上的电源线及通讯线, \n装好上盖、打上螺丝，完成后点通过", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
2704 OUT MCUPORT = "STAB:1"
2705 CHECK "AUTO"
2706 OUT MCUPORT = "STPB"


2709 LETSTR ERRMSG = "步骤20, LCD全屏显示测试不通过"
2710 REM =========STEP 20:  TEST LCD ==============
2711 OUT TUTORIAL = "FullScreen.JPG"
2712 OUT INSTRUCTION = "步骤20，插上电源，待测仪器关机模式下、\n长按退出键不放、同时按住电源键直到\nLCD全显示，检查LCD是否显示不良，完成后点通过", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
2713 DELAY 0
2714 OUT CONSOLE = "PASS"

2719 LETSTR ERRMSG = "步骤21, 按键测试不通过"
2722 OUT TUTORIAL = "KeyFunc.JPG"
2723 OUT INSTRUCTION = "步骤21，按读数键进入按键测试界面，\n分别按退出、设置、校正、读数键，\nLCD显示对应的功能键符号逐个消失，\n注意每次按键蜂鸣器都会响一声，完成后点通过", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
2724 DELAY 0
2726 OUT CONSOLE = "PASS"

2749 LETSTR ERRMSG = "步骤22, 打印序列号测试不通过"
2750 REM =========STEP 22:  PRINT report ==============
2751 OUT TUTORIAL = "ScanBarcodeEC.JPG"
2752 OUT INSTRUCTION = "步骤22，请扫描仪器序列号, 打印完成后点通过", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
2753 OUT CONSOLE = "_SCANEC"
2755 DELAY 0

2800 OUT TUTORIAL = "Packing.JPG"
2801 OUT INSTRUCTION = "步骤23，所有测试项目已通过，请贴\n上序列号，检查外观后包装", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
2802 CHECK "AUTO"

2850 OUT CONSOLE = "_CURRENTTIME"

2864 GOTO 10000


2999 REM ===== THIS IS CHECK THE CONDUCTIVITY ==================
3000 OUT DEVICEPORT = "?RD.EC"
3001 READDATA COND = "?RD.EC"
3002 OUT CONSOLE =  "read Cond=", COND
3003 IF COND < LOWLIMIT THEN 3100
3004 IF COND > HIGHLIMIT THEN 3100
3005 RETURN

3100 LETSTR AA = LOWLIMIT, "to",HIGHLIMIT, "us/cm test fail"
3101 OUT CONSOLE = AA
3103 LETSTR ERRMSG = MSG, " 测试不通过"
3105 GOTO 4010

3499 REM ===== THIS IS READING CALIBRATION EC OHM VALUE ========
3500 OUT DEVICEPORT = "?EC.OHM0"
3501 READDATA OHM0 = "?EC.OHM0"
3502 OUT CONSOLE =  "OHM0=", OHM0
3503 RETURN

3999 REM ===== THIS IS CHECK THE TEMPERATURE ==================
4000 OUT DEVICEPORT = CMDSTR
4001 READDATA VALUE = CMDSTR
4002 OUT CONSOLE =  CMDSTR, "=", VALUE
4003 IF VALUE < LOWLIMIT THEN 4010
4004 IF VALUE > HIGHLIMIT THEN 4010
4005 RETURN

4010 OUT CONSOLE = "_ERROR"

4050 STOP
4051 OUT CONSOLE = "_GETERRORCODE"
4052 READDATA ERRCODE = "_GETERRORCODE"
4053 IF ERRCODE = 1 THEN 4060
4054 IF ERRCODE = 0 THEN 4070
4055 GOTO 5000

4060 IF ERRPOS = 1 THEN 4070
4061 OUT INSTRUCTION = "测试意外终止！", COMMERRORSTR, "\nFONTCOLOR=RED", "\nFONTSIZE=24"
4062 GOTO 4100

4070 OUT CONSOLE = ERRMSG
4072 OUT INSTRUCTION = "错误！", ERRMSG, "\nFONTCOLOR=RED", "\nFONTSIZE=24"

4100 OUT MCUPORT = "STAB:2"
4105 DELAY 0
4107 OUT MCUPORT = "STPB"
4108 GOTO 10000

5000 OUT INSTRUCTION = "程序已停止！", "\nFONTCOLOR=BLUE", "\nFONTSIZE=24"
5001 OUT MCUPORT = "STPB"

10000 END
