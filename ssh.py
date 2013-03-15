# encoding: utf-8

from common import tester_base

class SSHDealer:
  def __init__(self, user, host, key = None):
    self.host = user + "@" + host
    self.key = [] if key is None else ["-i", key]
  
  def execute(self, cmd, **kargs):
    tester_base.execCommand(["ssh"] + self.key + [self.host, cmd], **kargs)
  
  def copyTo(self, source, dest):
    tester_base.execCommand(["scp"] + self.key + ["-r", source, self.host + ":" + dest])
  
  def copyFrom(self, source, dest):
    tester_base.execCommand(["scp"] + self.key + ["-r", self.host + ":" + source, dest])
