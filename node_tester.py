#!/usr/bin/python
# encoding: utf-8

from common import tester_base, paral
import node_config
import time, os, threading, optparse, signal, socket

def buildTestApp():
  log_prefix = "buildTestApp: "

  old_cwd = os.getcwd()
  os.chdir(os.path.join(tester_base.files_on_node, node_config.build_dir))
  
  tester_base.log("Building test grape application...", log_prefix)
  
  tester_base.execCommand(["make"])

  os.chdir(old_cwd)

def uploadApp(cocaine_conf, manifest, profile, archive_file, app_name):
  log_prefix = "uploadApp: "

  tester_base.log("Uploading application " + app_name + "...", log_prefix)
    
  tester_base.execCommand(["cocaine-tool", "-c", cocaine_conf, "-m", manifest, 
                           "-p", archive_file, "-n", app_name, "app:upload"])
  tester_base.execCommand(["cocaine-tool", "-c", cocaine_conf, "-m", profile, 
                          "-n", app_name, "profile:upload"])

def uploadTestApp():
  old_cwd = os.getcwd()
  os.chdir(os.path.join(tester_base.files_on_node, node_config.build_dir))

  uploadApp(os.path.join(node_config.working_dir,
                         tester_base.files_on_node,
                         node_config.cocaine_conf),
            node_config.manifest,
            node_config.profile,
            node_config.tar_name,
            "test-app")
  uploadApp(os.path.join(node_config.working_dir,
                         tester_base.files_on_node,
                         node_config.cocaine_conf),
            node_config.manifest,
            node_config.profile,
            node_config.tar_name,
            "test-app-second")
  
  os.chdir(old_cwd)

class DaemonDealer:
  def __init__(self, messenger):
    self.reader = messenger.makefile("r", bufsize = 0)
    self.writer = messenger.makefile("w", bufsize = 0)
    
    self.process = paral.Process(["dnet_ioserv",
                                  "-c",
                                  os.path.join(tester_base.files_on_node, node_config.elliptics_conf)])
    # container for result of tasks. must be mutable object.
    self.result = [None]
    # possible values of the result
    self.DAEMON_FAILED = 1
    self.SUCCESSFUL_TEST = 2
    # lock for access to self.result
    self.lock = threading.Lock()
    self.tasks = paral.MultiTaskPerformer([self.monitorDaemon, self.testElliptics])
  
  def performTest(self):
    self.tasks.start()
    self.tasks.joinAll()
    self.reader.close()
    self.writer.close()
  
  def isRunning(self):
    return self.process.isStarted() and self.process.poll() is None
  
  def resultOfTask(self, val):
    with self.lock:
      if self.result[0] is None:
        self.result[0] = val
  
  def monitorDaemon(self):
    log_prefix = "monitorDaemon: "
    
    tester_base.log("Starting elliptics daemon...", log_prefix)
    self.process.start()
    self.process.wait()
    
    self.resultOfTask(self.DAEMON_FAILED)
    tester_base.log("Daemon stoped.", log_prefix)

  def testElliptics(self):
    log_prefix = "testElliptics: "
    
    try:
      tester_base.log("Waiting 10 seconds for starting of the daemon...", log_prefix)
      time.sleep(10)
      
      if not self.isRunning():
        return
      
      tester_base.log("Elliptics is ready.", log_prefix)
      
      tester_base.writeLine("msg:daemon_prepared", f = self.writer)
      
      # event loop
      while self.isRunning():
        line = self.reader.readline()
        
        if line.rstrip("\n") == "msg:upload_app":
          buildTestApp()
          uploadTestApp()
          tester_base.writeLine("msg:application_uploaded", f = self.writer)
        elif len(line) == 0:
          break
      else:
        return
      
      self.resultOfTask(self.SUCCESSFUL_TEST)
    finally:
      if self.isRunning():
        tester_base.log("Killing the daemon...", log_prefix)
        self.process.kill()

def installPackages():
  tester_base.execCommand(["sudo", os.path.join(node_config.working_dir, "common/installer.py")] +
                          [p if v is None else p + "=" + v for p, v in node_config.packages])

def performTest(socket):
  installPackages()
  
  tester = DaemonDealer(socket)
  tester.performTest()
  tester_base.log("Test is finished.")
  
  if tester.result[0] == tester.DAEMON_FAILED:
    tester_base.log("Daemon failed.")
  elif tester.result[0] != tester.SUCCESSFUL_TEST:
    tester_base.error("Unexpected result of testing. Something is wrong.")

def processArgs():
  parser = optparse.OptionParser()
  parser.add_option("--deploy-test",
                    action = "store_true",
                    help = "build and deploy test application in elliptics")
  (options, args) = parser.parse_args()
  
  node_config.deploy_test = options.deploy_test

def main():
  processArgs()
  os.chdir(node_config.working_dir)
  signal.signal(signal.SIGINT, signal.SIG_IGN)
  
  tester_base.bindOutputToLog("tester.log")
  
  # wait for connection from main node
  tester_base.log("Tester will be listening on " + str(node_config.port) + " port.")
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind(("", node_config.port))
  s.listen(1)
  
  tester_base.log("Waiting for connection from main tester...")
  s.settimeout(15)
  messenger, addr = s.accept()
  messenger.settimeout(None)
  tester_base.log("Connection from " + str(addr) + " accepted.")
  
  try:
    performTest(messenger)
  finally:
    messenger.close()
  
#########################################################################
if __name__ == "__main__":
  main()
