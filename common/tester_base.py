# encoding: utf-8

import subprocess, sys, os

script_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
if script_dir[-1] != "/":
  script_dir += "/"

files_on_node = "files/"

class TesterException(Exception): pass
class ExecException(TesterException): pass

def writeLine(string, f = None):
  if f is None:
    f2 = sys.stdout
  else:
    f2 = f
    
  f2.write(string + "\n")
  f2.flush()

def log(message, prefix = ""):
  writeLine(prefix + message)

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

def bindOutputToLog(log_file):
  tee = subprocess.Popen(["tee", log_file], stdin=subprocess.PIPE)
  os.dup2(tee.stdin.fileno(), sys.stdout.fileno())
  os.dup2(tee.stdin.fileno(), sys.stderr.fileno())