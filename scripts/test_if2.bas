1 LET A = 1
3 LETSTR ASTR = "?NTC.A#", A
5 READDATA AVALUE = ASTR
7 PRINT AVALUE
9 READDATA BVALUE = "?AAA"
10 PRINT BVALUE
15 LETSTR CONSOLE = "CONSOLEs"
20 LETSTR CNSTR = "�¹ⲩ��"
100 LET A = 1.5678
105 LET LEFT = 1
110 LET RIGHT = 2
120 IF A < LEFT THEN 130
121 IF A > RIGHT THEN 130
125 OUT CONSOLE =  "A=", A
126 OUT CONSOLE = "A is between ", LEFT, " and ", RIGHT
127 OUT CONSOLE = CNSTR
130 GOTO 1000

1000 END
