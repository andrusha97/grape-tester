# encoding: utf-8

from common import tester_base

def copyToHost(host, source, dest, key = None):
  tester_base.execCommand(["scp"] +
                          ([] if key is None else ["-i", key]) +
                          ["-r", source, host + ":" + dest])

def copyFromHost(host, source, dest, key = None):
  tester_base.execCommand(["scp"] +
                          ([] if key is None else ["-i", key]) +
                          ["-r", host + ":" + source, dest])

def execOnHost(host, cmd, key = None):
  tester_base.execCommand(["ssh"] +
                          ([] if key is None else ["-i", key]) +
                          [host, cmd])
