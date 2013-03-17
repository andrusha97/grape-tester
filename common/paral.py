# encoding: utf-8

import subprocess, threading, socket
  
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

class Messenger:
  def __init__(self, f = None):
    self.channel = f
  
  def set(self, f):
    self.channel = f
  
  def state(self):
    if self.channel is None:
      return "not connected"
    elif self.channel.closed:
      return "disconnected"
    else:
      return "active"
  
  def read(self):
    if self.state() == "active":
      try:
        line = self.channel.readline()
        if len(line) > 0:
          return line.rstrip("\n")
      except socket.error:
        pass
      
    return None
  
  def write(self, msg):
    if self.state() == "active":
      try:
        print >> self.channel, msg
      except socket.error:
        pass
  
  def close(self):
    if self.state() == "active":
      try:
        self.channel.close()
      except socket.error:
        pass
