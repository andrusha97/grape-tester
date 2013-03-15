# encoding: utf-8

import subprocess, threading

class MultiTaskPerformer:
  def __init__(self, tasks, args = ()):
    self.threads = [threading.Thread(target = t, args = args)
                    for t in tasks]
                      
  def start(self):
    for t in self.threads:
        t.start()
  
  def joinAll(self):
    for t in self.threads:
      t.join()
  
class ProcessHandlingError(Exception): pass
  
class Process:
  def __init__(self, cmd, **popen_args):
    self.command = cmd
    self.popen_args = popen_args
    self.process = None
  
  def start(self):
    self.process = subprocess.Popen(self.command, **self.popen_args)
    
  def isStarted(self):
    return (self.process is not None)
  
  def poll(self):
    if self.isStarted():
      return self.process.poll()
    else:
      raise ProcessHandlingError("Process.poll: Process has not been started.")
  
  def wait(self):
    if self.isStarted():
      return self.process.wait()
    else:
      raise ProcessHandlingError("Process.wait: Process has not been started.")
  
  def communicate(self, input = None):
    if self.isStarted():
      return self.process.communicate(input)
    else:
      raise ProcessHandlingError("Process.communicate: Process has not been started.")
  
  def kill(self):
    if self.isStarted():
      return self.process.kill()
    else:
      raise ProcessHandlingError("Process.kill: Process has not been started.")
  
  def terminate(self):
    if self.isStarted():
      return self.process.terminate()
