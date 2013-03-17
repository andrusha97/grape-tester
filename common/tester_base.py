# encoding: utf-8

import subprocess, sys, os, logging

script_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
if script_dir[-1] != "/":
  script_dir += "/"

files_on_node = "files/"

class TesterException(Exception): pass
class ExecException(TesterException): pass

def error(message, logger = logging.getLogger(), exception = TesterException):
  logger.error("error: " + message)
  raise exception(message)

def execCommand(cmd, raise_on_error = True, **args):
  rcode = subprocess.call(cmd, **args)
  if rcode != 0 and raise_on_error:
    error("Command has ended with code " + str(rcode) + ": " + " ".join(cmd),
          exception = ExecException)
  else:
    return rcode

def bindOutputToFile(file):
  sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
  tee = subprocess.Popen(["tee", file], stdin=subprocess.PIPE)
  os.dup2(tee.stdin.fileno(), sys.stdout.fileno())
  os.dup2(tee.stdin.fileno(), sys.stderr.fileno())

def setupLogging(log_file):
  logging.basicConfig(level = logging.INFO, format = "%(message)s")
  logging.getLogger("paramiko.transport").setLevel(logging.WARNING)
  bindOutputToFile(log_file)