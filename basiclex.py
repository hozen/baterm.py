# An implementation of Dartmouth BASIC (1964)

from ply import *

keywords = (
    'LET','READ','DATA','PRINT','GOTO','IF','THEN','FOR','NEXT','TO','STEP',
    'END','STOP','DEF','GOSUB','DIM','REM','RETURN','RUN','LIST','NEW',
    'OUT','DELAY','LETSTR','CHECK','READDATA',
)

# list of token names. always required.
tokens = keywords + (
     'EQUALS','PLUS','MINUS','TIMES','DIVIDE','POWER',
     'LPAREN','RPAREN','LT','LE','GT','GE','NE',
     'COMMA','SEMI', 'INTEGER','FLOAT', 'STRING',
     'ID','NEWLINE'
)

# a string containing ignored characters (spaces and tabs)
t_ignore = ' \t'

def t_REM(t):
    r'REM .*'
    return t

def t_ID(t):
    r'[A-Z][A-Z0-9]*'
    if t.value in keywords:
        t.type = t.value
    return t

def t_OUT(t):
    r'OUT .*'
    return t

# regular expression rules for simple tokens    
t_EQUALS  = r'='
t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_POWER   = r'\^'
t_DIVIDE  = r'/'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_LT      = r'<'
t_LE      = r'<='
t_GT      = r'>'
t_GE      = r'>='
#t_LET     = r'xx'   # so LET can be instead by xx if uncomment.
t_NE      = r'<>'
t_COMMA   = r'\,'
t_SEMI    = r';'
t_INTEGER = r'\d+'    
t_FLOAT   = r'((\d*\.\d+)(E[\+-]?\d+)?|([1-9]\d*E[\+-]?\d+))'
t_STRING  = r'\".*?\"'  # using .*? will only match "xxx", but won't match "xxx""xxx"

def t_NEWLINE(t):
    r'\n'
    t.lexer.lineno += 1
    return t

def t_error(t):
    print("Illegal character %s" % t.value[0])
    t.lexer.skip(1)

lex.lex(debug=0)    #build the lexer
