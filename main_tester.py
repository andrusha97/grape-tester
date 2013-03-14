#!/usr/bin/python
# encoding: utf-8

from common import tester_base, installer, paral
import ssh_operations
import main_config, node_config
import os, sys, shutil, threading, subprocess, time, optparse, re, signal

def listAllFiles(dir):
  for d in os.walk(dir):
    for file in d[2]:
      yield os.path.join(d[0], file)

def preprocessDirectory(dir, env):
  for file in listAllFiles(dir):
    if file.endswith(".tmpl"):
      f1 = open(file, "r")
      f2 = open(os.path.splitext(file)[0], "w")
      f2.write(re.sub("<{(.*?)}>", lambda g: str(eval(g.group(1), env)), f1.read()))
      f2.close()
      f1.close()
      os.remove(file)

def prepareFilesForNodes():
  log_prefix = "prepareFilesForNodes: "
  tester_base.log("Preparing tester for uploading to nodes...", log_prefix)
  
  shutil.rmtree(main_config.nodes_dir, ignore_errors = True)
  
  # create folders for files (scripts, logs, etc) from nodes: nodes/0/, nodes/1/, ...
  for dname, node in enumerate(main_config.nodes):
    for_deploy = os.path.join(main_config.nodes_dir, str(dname), "to_deploy/")
    os.makedirs(for_deploy)
    
    shutil.copytree(main_config.node_files, os.path.join(for_deploy, tester_base.files_on_node))
    
    preprocessDirectory(os.path.join(for_deploy, tester_base.files_on_node),
                        {"node_config": node_config,
                         "main_config": main_config,
                         "node": node
                        })
    
    shutil.copytree(os.path.join(tester_base.script_dir, "common/"), os.path.join(for_deploy, "common/"))
    shutil.copy(os.path.join(tester_base.script_dir, "node_config.py"), for_deploy)
    shutil.copy(os.path.join(tester_base.script_dir, "node_tester.py"), for_deploy)
    
    tester_base.log("Node tester has been written to " + for_deploy, log_prefix)

def uploadTesterToNodes():
  log_prefix = "uploadTesterToNodes: "
  tester_base.log("Uploading tester to nodes...", log_prefix)
  
  for num, node in enumerate(main_config.nodes):
    ssh_operations.execOnHost(main_config.ssh_user + "@" + node, 
                              "rm -rf " + "'" + node_config.working_dir + "'",
                              key = main_config.ssh_key)
    ssh_operations.copyToHost(main_config.ssh_user + "@" + node, 
                              os.path.join(main_config.nodes_dir, str(num), "to_deploy/"), 
                              node_config.working_dir,
                              key = main_config.ssh_key)
    ssh_operations.execOnHost(main_config.ssh_user + "@" + node, 
                              "chmod +x " + "'" + os.path.join(node_config.working_dir, "common/installer.py") + "'",
                              key = main_config.ssh_key)

class NodeTester(paral.Process):
  def __init__(self, node, log_file, first_node = False):
    self.daemon_ready = threading.Lock()
    self.app_uploaded = threading.Lock()
    self.log_file = log_file
    self.dublicate = first_node
    self.start_status = None
    self.upload_status = None
    self.dr_locked = False
    self.au_locked = False
    
    paral.Process.__init__(self, 
                           ["ssh"] +
                           ([] if main_config.ssh_key is None else ["-i", main_config.ssh_key]) +
                           [main_config.ssh_user + "@" + node,
                            "python " +
                            "'" + os.path.join(node_config.working_dir, "node_tester.py") + "'" +
                            (" --deploy-test" if first_node else "")],
                           stdin = subprocess.PIPE,
                           stdout = subprocess.PIPE,
                           stderr = subprocess.STDOUT)
  
  def monitor(self):
    self.__acquireDRLock__()
    self.__acquireAULock__()

    try:
      log = open(self.log_file, "w", buffering = 0)
      
      while True:
        line = self.process.stdout.readline()
        if len(line) == 0:
          break
        elif line == "__msg__:node_tester:daemon_prepared\n":
          self.start_status = "ok"
          self.__daemonIsReady__()
        elif line == "__msg__:node_tester:application_uploaded\n":
          self.upload_status = "ok"
          self.__appUploaded__ ()
        else:
          if line[-1] == "\n":
            line = line[:-1]
          tester_base.writeLine(line, f = log)
          if self.dublicate:
            tester_base.log(line, "node: ")
    finally:
      self.__daemonIsReady__()
      self.__appUploaded__()
  
  def __acquireDRLock__(self):
    self.daemon_ready.acquire()
    self.dr_locked = True
  
  def __acquireAULock__(self):
    self.app_uploaded.acquire()
    self.au_locked = True
  
  def __daemonIsReady__(self):
    if self.dr_locked:
      self.daemon_ready.release()
      self.dr_locked = False
  
  def __appUploaded__(self):
    if self.au_locked:
      self.app_uploaded.release()
      self.au_locked = False
   
  def start(self):
    paral.Process.start(self)
    self.thread = threading.Thread(target = self.monitor)
    self.thread.start()
  
  def waitForStart(self):
    self.daemon_ready.acquire()
  
  def waitForUpload(self):
    self.app_uploaded.acquire()
  
  def testFinished(self):
    if self.start_status == "ok":
      tester_base.writeLine("__msg__:tester:tests_finished", f = self.process.stdin)
  
  def allDaemonsAreReady(self):
    if self.start_status == "ok":
      tester_base.writeLine("__msg__:tester:daemons_ready", f = self.process.stdin)
        

def testDaemon():
  log_prefix = "testDaemon: "
  
  daemons = []
  for num, node in enumerate(main_config.nodes):
    daemons.append(NodeTester(node,
                              os.path.join(main_config.nodes_dir, str(num), "tester.log"),
                              first_node = (num == 0)))
  
  tester_base.log("Starting testers on nodes...", log_prefix)
  for d in daemons:
    d.start()
  
  try:
    tester_base.log("Waiting for testers on nodes...", log_prefix)
    
    ok = True
    for d in daemons:
      d.waitForStart()
      
    fail = filter(lambda x: x[1].
                  start_status != "ok", enumerate(daemons))
    
    if len(fail) == 0:
      tester_base.log("Waiting 5 seconds after starting of daemons...", log_prefix)
      time.sleep(5)
      
      daemons[0].allDaemonsAreReady()
      daemons[0].waitForUpload()
      
      if daemons[0].upload_status != "ok":
        tester_base.error("Application has not been uploaded.", log_prefix)
      
      tester_base.log("Waiting 5 seconds after uploading of application...", log_prefix)
      time.sleep(5)
      
      tester_base.log("Elliptics is ready. Launching test application...", log_prefix)
      
      tester_base.execCommand(("dnet_ioclient -r " + main_config.nodes[0] + ":1025:2 -g2 -c test-app@start-task").split())
      tester_base.execCommand(("dnet_ioclient -r " + main_config.nodes[0] + ":1025:2 -g2 -c test-app-second@start-task").split())
      
      output = subprocess.check_output(("dnet_ioclient -r " + main_config.nodes[0] + ":1025:2 -g2 -c").split() + ["test-app@event0 xxx"])
      
      tester_base.execCommand(("dnet_ioclient -r " + main_config.nodes[0] + ":1025:2 -g2 -c test-app-second@stop-task").split())
      tester_base.execCommand(("dnet_ioclient -r " + main_config.nodes[0] + ":1025:2 -g2 -c test-app@stop-task").split())
      
      if output != \
         'xxx123test-app-second@event0|test-app-second@event1|test-app-second@event2|test-app-second@finish|':
        tester_base.error("dnet_ioclient returned string '" + output + "'. something is wrong.", log_prefix)
      else:
        tester_base.log("Test has been successfully completed.", log_prefix)
        
    else:
      tester_base.error("Following node testers finished with error: " + ', '.join([str(n[0]) for n in fail]), log_prefix)
      
  finally:
    tester_base.log("Stopping testers on nodes...", log_prefix)
    for d in daemons:
      d.testFinished()
    for d in daemons:
      d.thread.join()

def downloadFilesFromNodes():
  log_prefix = "downloadFilesFromNodes: "
  tester_base.log("Downloading working directories (with logs, configs, etc) from nodes...", log_prefix)
  #tester_base.log("You can find them in nodes/{0, 1, ...}/" + tester_base.files_on_node + ".", log_prefix)
  
  for num, node in enumerate(main_config.nodes):
    for f in main_config.remove_before_downloading:
      ssh_operations.execOnHost(main_config.ssh_user + "@" + node, 
                                "rm -rf " + "'" + os.path.join(node_config.working_dir, f) + "'",
                                key = main_config.ssh_key)
    
    ssh_operations.copyFromHost(main_config.ssh_user + "@" + node,
                                os.path.join(node_config.working_dir, tester_base.files_on_node),
                                os.path.join(main_config.nodes_dir, str(num)),
                                key = main_config.ssh_key)

def installPackages():
  args = []
  for p, v in main_config.packages:
    if v is None:
      args.append(p)
    else:
      args.append(p + "=" + v)
  
  tester_base.execCommand(["sudo", os.path.join(tester_base.script_dir, "common/installer.py")] + args)

def processArgs():
  parser = optparse.OptionParser()
  parser.add_option("-k",
                      "--key",
                      default = main_config.ssh_key,
                      help = "file with private key for access to nodes over ssh")
  (options, args) = parser.parse_args()
  main_config.ssh_key = options.key

def main():
  os.putenv("LC_ALL", "C.UTF-8")
  signal.signal(signal.SIGINT, signal.SIG_IGN)
  
  processArgs()
  
  if len(main_config.nodes) == 0:
    tester_base.log("List of nodes in main_config.py is empty.")
    return
  
  # duplicate stdout and stderr to log
  tee = subprocess.Popen(["tee", main_config.log_file], stdin=subprocess.PIPE)
  sys.stdout = tee.stdin
  sys.stderr = tee.stdin
  
  installPackages()
  prepareFilesForNodes()
  uploadTesterToNodes()
  try:
    testDaemon()
  finally:
    downloadFilesFromNodes()
    tester_base.log("You can find files from nodes in '" +
                    os.path.join(main_config.nodes_dir, "{0, 1, ...}", tester_base.files_on_node) + "', " +
                    "logs of node testers in '" +
                    os.path.join(main_config.nodes_dir, "{0, 1, ...}", "tester.log") + "', " +
                    "log of this script in '" + main_config.log_file + "'.")
  
  tester_base.log("Success!")

if __name__ == "__main__":
  main()
  