# This file provides the runtime support for running a basic program
# Assumes the program has been parsed using basparse.py

import sys
import math
import random
import time
import re

class BasicInterpreter:

    # Initialize the interpreter. prog is a dictionary
    # containing (line,statement) mappings
    def __init__(self, prog, instance):
         self.prog = prog
         self.cali = instance
         
         self.functions = {           # Built-in function table
             'SIN' : lambda z: math.sin(self.eval(z)),
             'COS' : lambda z: math.cos(self.eval(z)),
             'TAN' : lambda z: math.tan(self.eval(z)),
             'ATN' : lambda z: math.atan(self.eval(z)),
             'EXP' : lambda z: math.exp(self.eval(z)),
             'ABS' : lambda z: abs(self.eval(z)),
             'LOG' : lambda z: math.log(self.eval(z)),
             'SQR' : lambda z: math.sqrt(self.eval(z)),
             'INT' : lambda z: int(self.eval(z)),
             'RND' : lambda z: random.random()
         }

    # Collect all data statements
    def collect_data(self):
         self.data = []
         for lineno in self.stat:
              if self.prog[lineno][0] == 'DATA':
                  self.data = self.data + self.prog[lineno][1]
         self.dc = 0                  # Initialize the data counter
         
    # Check for end statements
    def check_end(self):
         has_end = 0
         for lineno in self.stat:
             if self.prog[lineno][0] == 'END' and not has_end:
                  has_end = lineno
         if not has_end:
             print("NO END INSTRUCTION")
             self.error = 1
             return
         if has_end != lineno:
             print("END IS NOT LAST")
             self.error = 1
    
    def get_stop_pc(self):  # get and check
        has_stop = 0
        pc = 0
        for lineno in self.stat:
            pc += 1
            if self.prog[lineno][0] == 'STOP':
                has_stop = 1
                break
        if not has_stop: return 0
        else: return (pc-1)

        
    # Check loops
    def check_loops(self):
         for pc in range(len(self.stat)):
             lineno = self.stat[pc]
             if self.prog[lineno][0] == 'FOR':
                  forinst = self.prog[lineno]
                  loopvar = forinst[1]
                  for i in range(pc+1,len(self.stat)):
                       if self.prog[self.stat[i]][0] == 'NEXT':
                            nextvar = self.prog[self.stat[i]][1]
                            if nextvar != loopvar: continue
                            self.loopend[pc] = i
                            break
                  else:
                       print("FOR WITHOUT NEXT AT LINE %s" % self.stat[pc])
                       self.error = 1
                  
    # Evaluate an expression
    def eval(self,expr):
        etype = expr[0]
        if etype == 'NUM': return expr[1]
        elif etype == 'GROUP': return self.eval(expr[1])
        elif etype == 'UNARY':
             if expr[1] == '-': return -self.eval(expr[2])
        elif etype == 'BINOP':
             if expr[1] == '+': return self.eval(expr[2])+self.eval(expr[3])
             elif expr[1] == '-': return self.eval(expr[2])-self.eval(expr[3])
             elif expr[1] == '*': return self.eval(expr[2])*self.eval(expr[3])
             elif expr[1] == '/': return float(self.eval(expr[2]))/self.eval(expr[3])
             elif expr[1] == '^': return abs(self.eval(expr[2]))**self.eval(expr[3])
        elif etype == 'VAR':
             var,dim1,dim2 = expr[1]
             if not dim1 and not dim2:
                  if var in self.vars:
                       return self.vars[var]
                  else:
                       print("UNDEFINED VARIABLE %s AT LINE %s" % (var, self.stat[self.pc]))
                       raise RuntimeError
             # May be a list lookup or a function evaluation
             if dim1 and not dim2:
                if var in self.functions:
                      # A function
                      return self.functions[var](dim1)
                else:
                      # A list evaluation
                      if var in self.lists:
                            dim1val = self.eval(dim1)
                            if dim1val < 1 or dim1val > len(self.lists[var]):
                                 print("LIST INDEX OUT OF BOUNDS AT LINE %s" % self.stat[self.pc])
                                 raise RuntimeError
                            return self.lists[var][dim1val-1]
             if dim1 and dim2:
                 if var in self.tables:
                      dim1val = self.eval(dim1)
                      dim2val = self.eval(dim2)
                      if dim1val < 1 or dim1val > len(self.tables[var]) or dim2val < 1 or dim2val > len(self.tables[var][0]):
                           print("TABLE INDEX OUT OUT BOUNDS AT LINE %s" % self.stat[self.pc])
                           raise RuntimeError
                      return self.tables[var][dim1val-1][dim2val-1]
             print("UNDEFINED VARIABLE %s AT LINE %s" % (var, self.stat[self.pc]))
             raise RuntimeError

    # Evaluate a relational expression
    def releval(self,expr):
         etype = expr[1]
         lhs   = self.eval(expr[2])
         rhs   = self.eval(expr[3])

         if etype == '<':
             if lhs < rhs: return 1
             else: return 0

         elif etype == '<=':
             if lhs <= rhs: return 1
             else: return 0

         elif etype == '>':
             if lhs > rhs: return 1
             else: return 0

         elif etype == '>=':
             if lhs >= rhs: return 1
             else: return 0

         elif etype == '=':
             if lhs == rhs: return 1
             else: return 0

         elif etype == '<>':
             if lhs != rhs: return 1
             else: return 0

    # Assignment
    def assign(self,target,value):
        var, dim1, dim2 = target
        if not dim1 and not dim2:
            self.vars[var] = self.eval(value)
        elif dim1 and not dim2:
            # List assignment
            dim1val = self.eval(dim1)
            if not var in self.lists:
                 self.lists[var] = [0]*10

            if dim1val > len(self.lists[var]):
                 print ("DIMENSION TOO LARGE AT LINE %s" % self.stat[self.pc])
                 raise RuntimeError
            self.lists[var][dim1val-1] = self.eval(value)
        elif dim1 and dim2:
            dim1val = self.eval(dim1)
            dim2val = self.eval(dim2)
            if not var in self.tables:
                 temp = [0]*10
                 v = []
                 for i in range(10): v.append(temp[:])
                 self.tables[var] = v
            # Variable already exists
            if dim1val > len(self.tables[var]) or dim2val > len(self.tables[var][0]):
                 print("DIMENSION TOO LARGE AT LINE %s" % self.stat[self.pc])
                 raise RuntimeError
            self.tables[var][dim1val-1][dim2val-1] = self.eval(value)

    # Change the current line number
    def goto(self,linenum):
         if not linenum in self.prog:
              print("UNDEFINED LINE NUMBER %d AT LINE %d" % (linenum, self.stat[self.pc]))
              raise RuntimeError
         self.pc = self.stat.index(linenum)

    # Run it
    def run(self):
        self.vars   = { }            # All variables
        self.curarr = [ ]            # Current 1 array only
        self.lists  = { }            # List variables
        self.tables = { }            # Tables
        self.loops  = [ ]            # Currently active loops
        self.loopend= { }            # Mapping saying where loops end
        self.gosub  = None           # Gosub return point (if any)
        self.error  = 0              # Indicates program error

        self.stat = list(self.prog)  # Ordered list of all line numbers

        self.stat.sort()
        self.pc = 0                  # Current program counter
        pc_of_end = len(self.stat) - 1
        pc_of_stop = self.get_stop_pc()
        if not pc_of_stop: pc_of_stop = pc_of_end
        # Processing prior to running

        self.collect_data()          # Collect all of the data statements
        self.check_end()
        self.check_loops()

        if self.error: 
            raise RuntimeError
        has_error = 0
        while 1:
            if self.cali.get_check_status() != 0 and not has_error:
                #break
                has_error = 1
                self.pc = pc_of_stop
                            
            line  = self.stat[self.pc]
            instr = self.prog[line]            
            op = instr[0]

            # END and STOP statements
            #if op == 'END' or op == 'STOP':
            if op == 'END':
                #print "ply end"    
                break           # We're done                        
                
            elif op == 'OUT':   # todo : it's better to use Console as the only comm tunnel between script and gui.
                text = ""      
                port = self.eval(instr[1])
                portvar = instr[1][1][0]
                #for label, val in instr[2]:
                #    if label == '':
                #        cmd = self.eval(val)
                #    else:
                #        cmd = label
                plist = instr[2]
                out = ""
                for label,val in plist:
                    if out:
                         out += ''*(15 - (len(out) % 15))
                    out += label
                    if val:
                         if label: out += " "
                         eval = self.eval(val)
                         out += str(eval)
                cmd = out
                if portvar == "CONSOLE":
                    self.cali.set_console_text(str(cmd))
                elif portvar == "TUTORIAL":
                    self.cali.set_tutorial(str(cmd))
                elif portvar == "INSTRUCTION":
                    self.cali.set_instruction(str(cmd))
                elif portvar == "FLASH":
                    self.cali.flash_msp430(str(cmd))
                else:
                    self.cali.set_console_text(port + " " + str(cmd))
                    
#                    if not self.vars.has_key("CHECK"):
#                        self.vars['CHECK'] = "AUTO"
#                    if not self.vars.has_key("MCUBAUD"):
#                        self.vars["MCUBAUD"] = 9600
#                    if not self.vars.has_key("DEVICEBAUD"):
#                        self.vars["DEVICEBAUD"] = 9600
#
#                    self.cali.ack_to_plying = 1
#                    if portvar == "MCUPORT":
#                        uart_conn_result = self.cali.set_uart_text(port, self.vars['MCUBAUD'], self.vars['CHECK'], str(cmd))
#                    elif portvar == "DEVICEPORT":
#                        uart_conn_result = self.cali.set_uart_text(port, self.vars['DEVICEBAUD'], self.vars['CHECK'], str(cmd))
#                    else:
#                        uart_conn_result = 1
#                    if uart_conn_result == 1:
#                        self.pc = pc_of_end - 1
#                    else:
#                        while True:                            
#                            if self.cali.ack_to_plying == 0 or self.cali.get_check_status() != 0:
#                                break
#                            time.sleep(0.01)

            elif op == 'DELAY':
                cmd = self.eval(instr[1])
                if cmd == 0:
                    self.cali.condition.acquire()                    
                    #print "ply condition acquired"
                    #while (self.cali.get_ack_to_plying() != 0 and self.cali.get_check_status() == 0):
                    try:
                        #print "ply condition waiting"                        
                        self.cali.condition.wait()
                        self.cali.condition.release()
                    except: 
                        print "ply condition wait error.."
                    #print "ply condition released"
                    #if self.cali.get_check_status() != 0:
                    #    self.pc = pc_of_stop - 1
                    #    print self.pc
                else:
                    time.sleep(cmd)
            
            elif op == 'LETSTR':
                var = instr[1][0]
                
                #for label, val in instr[2]:
                #    value = label
                
                plist = instr[2]
                out = ""
                for label,val in plist:
                    if out:
                         out += ''*(15 - (len(out) % 15))
                    out += label
                    if val:
                         if label: out += " "
                         eval = self.eval(val)
                         out += str(eval)
                cmd = out
                self.vars[var] = cmd
            elif op == 'READDATA':
                print instr
                var = instr[1][0]
                plist = instr[2]
                out = ""
                for label,val in plist:
                    if out:
                         out += ''*(15 - (len(out) % 15))
                    out += label
                    if val:
                         if label: out += " "
                         eval = self.eval(val)
                         out += str(eval)
                cmd = out
                #for label, val in instr[2]:
                #    value = label        
                #self.vars[var] = self.cali.get_batching_result(cmd)
                value = self.cali.get_batching_result(cmd)
                if type(value) is list:
                    self.curarr = value
                    self.vars[var] = value[0]
                else:                                        
                    self.vars[var] = value
                                
            elif op == 'CHECK':
                for label, val in instr[1]:
                    method = label
                self.vars['CHECK'] = method
                
            # GOTO statement
            elif op == 'GOTO':
                 newline = instr[1]
                 self.goto(newline)
                 continue

            # PRINT statement
            elif op == 'PRINT':
                 plist = instr[1]
                 out = ""
                 for label,val in plist:
                     if out:
                          out += ' '*(15 - (len(out) % 15))
                     out += label
                     if val:
                          if label: out += " "
                          eval = self.eval(val)
                          out += str(eval)
                 #sys.stdout.write(out)
                 self.cali.set_console_text(str(out))

                 end = instr[2]
                 if not (end == ',' or end == ';'): 
                     #sys.stdout.write("\n")
                     self.cali.set_console_text("\n")
                 #if end == ',': sys.stdout.write(" "*(15-(len(out) % 15)))
                 #if end == ';': sys.stdout.write(" "*(3-(len(out) % 3)))
                 if end == ',': self.cali.set_console_text(" "*(15-(len(out) % 15)))
                 if end == ';': self.cali.set_console_text(" "*(3-(len(out) % 3)))
                     
            # LET statement
            elif op == 'LET':
                 target = instr[1]
                 value  = instr[2]
                 self.assign(target,value)

            # READ statement
            elif op == 'READ':
                 #print "read instr" 
                 #print instr
                 #print self.data
                 for target in instr[1]:
                      if self.dc < len(self.data):
                          value = ('NUM',self.data[self.dc])
                          self.assign(target,value)
                          self.dc += 1
                      else:
                          # No more data.  Program ends
                          # todo : if use DATA 1 2 3 4 in script, need to check if it conflits
                          if len(self.curarr) > 0:
                              value = ('NUM', self.curarr.pop(0))
                              self.assign(target, value)
                          # todo : end
                          #return
            elif op == 'IF':
                 relop = instr[1]
                 newline = instr[2]
                 if (self.releval(relop)):
                     self.goto(newline)
                     continue

            elif op == 'FOR':
                 loopvar = instr[1]
                 initval = instr[2]
                 finval  = instr[3]
                 stepval = instr[4]
              
                 # Check to see if this is a new loop
                 if not self.loops or self.loops[-1][0] != self.pc:
                        # Looks like a new loop. Make the initial assignment
                        newvalue = initval
                        self.assign((loopvar,None,None),initval)
                        if not stepval: stepval = ('NUM',1)
                        stepval = self.eval(stepval)    # Evaluate step here
                        self.loops.append((self.pc,stepval))
                 else:
                        # It's a repeat of the previous loop
                        # Update the value of the loop variable according to the step
                        stepval = ('NUM',self.loops[-1][1])
                        newvalue = ('BINOP','+',('VAR',(loopvar,None,None)),stepval)

                 if self.loops[-1][1] < 0: relop = '>='
                 else: relop = '<='
                 if not self.releval(('RELOP',relop,newvalue,finval)):
                      # Loop is done. Jump to the NEXT
                      self.pc = self.loopend[self.pc]
                      self.loops.pop()
                 else:
                      self.assign((loopvar,None,None),newvalue)

            elif op == 'NEXT':
                 if not self.loops:
                       print("NEXT WITHOUT FOR AT LINE %s" % line)
                       return
 
                 nextvar = instr[1]
                 self.pc = self.loops[-1][0]
                 loopinst = self.prog[self.stat[self.pc]]
                 forvar = loopinst[1]
                 if nextvar != forvar:
                       print("NEXT DOESN'T MATCH FOR AT LINE %s" % line)
                       return
                 continue
            elif op == 'GOSUB':
                 newline = instr[1]
                 if self.gosub:
                       print("ALREADY IN A SUBROUTINE AT LINE %s" % line)
                       return
                 self.gosub = self.stat[self.pc]
                 self.goto(newline)
                 continue

            elif op == 'RETURN':
                 if not self.gosub:
                      print("RETURN WITHOUT A GOSUB AT LINE %s" % line)
                      return
                 self.goto(self.gosub)
                 self.gosub = None

            elif op == 'FUNC':
                 fname = instr[1]
                 pname = instr[2]
                 expr  = instr[3]
                 def eval_func(pvalue,name=pname,self=self,expr=expr):
                      self.assign((pname,None,None),pvalue)
                      return self.eval(expr)
                 self.functions[fname] = eval_func

            elif op == 'DIM':
                 for vname,x,y in instr[1]:
                     if y == 0:
                          # Single dimension variable
                          self.lists[vname] = [0]*x
                     else:
                          # Double dimension variable
                          temp = [0]*y
                          v = []
                          for i in range(x):
                              v.append(temp[:])
                          self.tables[vname] = v

            self.pc += 1   
            time.sleep(0.01)      

    # Utility functions for program listing
    def expr_str(self,expr):
        etype = expr[0]
        if etype == 'NUM': return str(expr[1])
        elif etype == 'GROUP': return "(%s)" % self.expr_str(expr[1])
        elif etype == 'UNARY':
             if expr[1] == '-': return "-"+str(expr[2])
        elif etype == 'BINOP':
             return "%s %s %s" % (self.expr_str(expr[2]),expr[1],self.expr_str(expr[3]))
        elif etype == 'VAR':
              return self.var_str(expr[1])

    def relexpr_str(self,expr):
         return "%s %s %s" % (self.expr_str(expr[2]),expr[1],self.expr_str(expr[3]))

    def var_str(self,var):
         varname,dim1,dim2 = var
         if not dim1 and not dim2: return varname
         if dim1 and not dim2: return "%s(%s)" % (varname, self.expr_str(dim1))
         return "%s(%s,%s)" % (varname, self.expr_str(dim1),self.expr_str(dim2))

    # Create a program listing
    def list(self):
         stat = list(self.prog)      # Ordered list of all line numbers
         stat.sort()
         for line in stat:
             instr = self.prog[line]
             op = instr[0]
             if op in ['END','STOP','RETURN']:
                   print("%s %s" % (line, op))
                   continue
             elif op == 'REM':
                   print("%s %s" % (line, instr[1]))
             elif op == 'PRINT':
                   _out = "%s %s " % (line, op)
                   first = 1
                   for p in instr[1]:
                         if not first: _out += ", "
                         if p[0] and p[1]: _out += '"%s"%s' % (p[0],self.expr_str(p[1]))
                         elif p[1]: _out += self.expr_str(p[1])
                         else: _out += '"%s"' % (p[0],)
                         first = 0
                   if instr[2]: _out += instr[2]
                   print(_out)
             elif op == 'LET':
                   print("%s LET %s = %s" % (line,self.var_str(instr[1]),self.expr_str(instr[2])))
             elif op == 'READ':
                   _out = "%s READ " % line
                   first = 1
                   for r in instr[1]:
                         if not first: _out += ","
                         _out += self.var_str(r)
                         first = 0
                   print(_out)
             elif op == 'IF':
                   print("%s IF %s THEN %d" % (line,self.relexpr_str(instr[1]),instr[2]))
             elif op == 'GOTO' or op == 'GOSUB':
                   print("%s %s %s" % (line, op, instr[1]))
             elif op == 'FOR':
                   _out = "%s FOR %s = %s TO %s" % (line,instr[1],self.expr_str(instr[2]),self.expr_str(instr[3]))
                   if instr[4]: _out += " STEP %s" % (self.expr_str(instr[4]))
                   print(_out)
             elif op == 'NEXT':
                   print("%s NEXT %s" % (line, instr[1]))
             elif op == 'FUNC':
                   print("%s DEF %s(%s) = %s" % (line,instr[1],instr[2],self.expr_str(instr[3])))
             elif op == 'DIM':
                   _out = "%s DIM " % line
                   first = 1
                   for vname,x,y in instr[1]:
                         if not first: _out += ","
                         first = 0
                         if y == 0:
                               _out += "%s(%d)" % (vname,x)
                         else:
                               _out += "%s(%d,%d)" % (vname,x,y)
                         
                   print(_out)
             elif op == 'DATA':
                   _out = "%s DATA " % line
                   first = 1
                   for v in instr[1]:
                        if not first: _out += ","
                        first = 0
                        _out += v
                   print(_out)

    # Erase the current program
    def new(self):
         self.prog = {}
 
    # Insert statements
    def add_statements(self,prog):
         for line,stat in prog.items():
              self.prog[line] = stat

    # Delete a statement
    def del_line(self,lineno):
         try:
             del self.prog[lineno]
         except KeyError:
             pass

