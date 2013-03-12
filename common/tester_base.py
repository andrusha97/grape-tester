# encoding: utf-8

import subprocess, sys

class TesterException(Exception): pass
class ExecException(TesterException): pass

def readLine(f = None):
  if f is None:
    f2 = sys.stdin
  else:
    f2 = f
    
  s = f2.readline()
  if len(s) > 0 and s[-1] == "\n":
    return s[:-1]
  else:
    return s

def writeLine(string, f = None):
  if f is None:
    f2 = sys.stdout
  else:
    f2 = f
    
  f2.write(string + "\n")
  f2.flush()

def log(message, prefix = ""):
  writeLine(prefix + message)
  #writeLine("log:" + prefix + message)

def error(message, prefix = "" , exception = TesterException):
  log(message, prefix = prefix + "error: ")
  raise exception(message)

def execCommand(cmd, raise_on_error = True, **args):
  rcode = subprocess.call(cmd, **args)
  if rcode != 0 and raise_on_error:
    error("Command has ended with code " + str(rcode) + ": " + " ".join(cmd), 
          "execCommand: ", 
          ExecException)
  else:
    return rcode