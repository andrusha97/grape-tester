#!/usr/bin/python
# encoding: utf-8

from common import tester_base, paral
import node_config
import time, os, signal, socket, logging

class NodeTester:
  def __init__(self, messenger):
    # for communication with main node
    self.messenger = paral.Messenger(messenger)
    
    self.process = paral.Process(["dnet_ioserv",
                                  "-c",
                                  os.path.join(tester_base.files_on_node, node_config.elliptics_conf)])
  
  def installPackages(self):
    tester_base.execCommand(["sudo", os.path.join(node_config.working_dir, "common/installer.py")] +
                            [p if v is None else p + "=" + v for p, v in node_config.packages])
  
  def buildTestApp(self):
    old_cwd = os.getcwd()
    os.chdir(os.path.join(tester_base.files_on_node, node_config.build_dir))
    
    logging.info("Building test grape application...")
    
    tester_base.execCommand(["make"])
  
    os.chdir(old_cwd)
  
  def uploadApp(self, cocaine_conf, manifest, profile, archive_file, app_name):
    logging.info("Uploading application '%s'..." % app_name)
      
    tester_base.execCommand(["cocaine-tool", "-c", cocaine_conf, "-m", manifest, 
                             "-p", archive_file, "-n", app_name, "app:upload"])
    tester_base.execCommand(["cocaine-tool", "-c", cocaine_conf, "-m", profile, 
                            "-n", app_name, "profile:upload"])
  
  def uploadTestApp(self):
    old_cwd = os.getcwd()
    os.chdir(os.path.join(tester_base.files_on_node, node_config.build_dir))
  
    self.uploadApp(os.path.join(node_config.working_dir,
                                tester_base.files_on_node,
                                node_config.cocaine_conf),
                   node_config.manifest,
                   node_config.profile,
                   node_config.tar_name,
                   "test-app")
    self.uploadApp(os.path.join(node_config.working_dir,
                                tester_base.files_on_node,
                                node_config.cocaine_conf),
                   node_config.manifest,
                   node_config.profile,
                   node_config.tar_name,
                   "test-app-second")
    
    os.chdir(old_cwd)
  
  def startDaemon(self):
    logging.info("Starting elliptics daemon...")
    self.process.start()
    
    logging.info("Waiting 7 seconds for starting of the daemon...")
    time.sleep(7)
    
    if not self.checkDaemon():
      tester_base.error("Daemon has failed to start.")
  
  def checkDaemon(self):
    return self.process.isStarted() and self.process.poll() is None
  
  def killDaemon(self):
    if self.checkDaemon():
      self.process.kill()
  
  def waitDaemon(self):
    if self.process.isStarted():
      self.process.wait()
  
  def run(self):
    try:
      while True:
        message = self.messenger.read()
        logging.debug("Message received: " + str(message))
        
        if message == "msg:install_packages":
          self.installPackages()
          self.messenger.write("msg:ok")
        elif message == "msg:run_elliptics":
          self.startDaemon()
          self.messenger.write("msg:ok")
        elif message == "msg:build_app":
          self.buildTestApp()
          self.messenger.write("msg:ok")
        elif message == "msg:upload_app":
          self.uploadTestApp()
          self.messenger.write("msg:ok")
        elif message == "msg:check_daemon":
          if self.checkDaemon():
            self.messenger.write("msg:ok")
          else:
            self.messenger.write("msg:does_not_work")
        elif message == "msg:wait_daemon":
          self.waitDaemon()
          self.messenger.write("msg:ok")
        elif message == "msg:kill_daemon":
          self.killDaemon()
          self.messenger.write("msg:ok")
        elif message == "msg:bye":
          logging.info("Main node has finished communication.")
          break
        elif message is None:
          tester_base.error("Main node has been unexpectedly finished.")
          break
        else:
          logging.warning("Unknown command '%s' received. Something is wrong." % message)
    finally:
      self.killDaemon()

def getMessenger():
  # wait for connection from main node
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind(("", node_config.port))
  s.listen(1)
  
  logging.info("Waiting for connection from main tester on %d port..." % node_config.port)
  s.settimeout(15)
  messenger, addr = s.accept()
  messenger.settimeout(None)
  logging.info("Connection from " + str(addr) + " accepted.")
  
  return messenger.makefile("w+", bufsize = 1)

def main():
  signal.signal(signal.SIGINT, signal.SIG_IGN)
  os.chdir(node_config.working_dir)
  tester_base.setupLogging("tester.log")
  
  messenger = getMessenger()
  
  try:
    tester = NodeTester(messenger)
    tester.run()
  finally:
    logging.info("Test is completed.")
    messenger.close()
  
#########################################################################
if __name__ == "__main__":
  main()
