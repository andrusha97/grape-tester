#!/usr/bin/python
# encoding: utf-8

from common import tester_base, installer, paral
from main_node import preprocessor, ssh_operations
import main_config, node_config
import os, sys, shutil, threading, subprocess, time

def ensureDir(fname):
  dname = os.path.dirname(fname)
  if not os.path.exists(dname):
    os.makedirs(dname)

def prepareFilesForNodes():
  log_prefix = "prepareFilesForNodes: "
  tester_base.log("Preparing tester for uploading to nodes...", log_prefix)
  
  shutil.rmtree(main_config.nodes_dir, ignore_errors = True)
  
  # create folders for files (scripts, logs, etc) from nodes: nodes/0/, nodes/1/, ...
  for dname, node in enumerate(main_config.nodes):
    for_deploy = main_config.nodes_dir + str(dname) + "/for_deploy/"
    os.makedirs(for_deploy)
    
    # create tester for nodes. directory nodes/N/for_deploy/ will be copied to Nth node.
    
    elliptics_conf = for_deploy + node_config.elliptics_conf
    cocaine_conf = for_deploy + node_config.cocaine_conf
    cpp_name = for_deploy + node_config.build_dir + node_config.cpp_name
    manifest = for_deploy + node_config.build_dir + node_config.manifest
    profile = for_deploy + node_config.build_dir + node_config.profile
    
    ensureDir(elliptics_conf)
    ensureDir(cocaine_conf)
    ensureDir(cpp_name)
    ensureDir(manifest)
    ensureDir(profile)
    ensureDir(for_deploy + node_config.logs_dir)
    ensureDir(for_deploy + node_config.leveldb_dir)
    ensureDir(for_deploy + node_config.history_dir)
    ensureDir(for_deploy + node_config.srv_dir)
    
    subst = [("<{NODES}>", ', '.join([n + ":1025:2" for n in main_config.nodes])),
             ("<{COCAINE_CONF}>", node_config.working_dir + node_config.cocaine_conf),
             ("<{LOGS}>", node_config.working_dir + node_config.logs_dir),
             ("<{HISTORY}>", node_config.working_dir + node_config.history_dir),
             ("<{LEVELDB}>", node_config.working_dir + node_config.leveldb_dir),
             ("<{SRV}>", node_config.working_dir + node_config.srv_dir),
             ("<{NODE}>", node),
             ("<{TEST_SONAME}>", node_config.soname)]
    
    preprocessor.processFile(main_config.elliptics_conf, elliptics_conf, subst)
    preprocessor.processFile(main_config.cocaine_conf, cocaine_conf, subst)
    preprocessor.processFile(main_config.test_cpp, cpp_name, subst)
    preprocessor.processFile(main_config.test_manifest, manifest, subst)
    preprocessor.processFile(main_config.test_profile, profile, subst)
    
    shutil.copytree(tester_base.script_dir + "common/", for_deploy + "common/")
    shutil.copy(tester_base.script_dir + "node_config.py", for_deploy)
    shutil.copy(tester_base.script_dir + "node_tester.py", for_deploy)
    
    tester_base.log("Node tester has been written to " + for_deploy, log_prefix)

def uploadTesterToNodes():
  log_prefix = "uploadTesterToNodes: "
  tester_base.log("Uploading tester to nodes...", log_prefix)
  
  for num, node in enumerate(main_config.nodes):
    ssh_operations.execOnHost(main_config.ssh_user + "@" + node, 
                              "rm -rf " + "'" + node_config.working_dir + "'",
                              key = main_config.ssh_key)
    ssh_operations.copyToHost(main_config.ssh_user + "@" + node, 
                              main_config.nodes_dir + str(num) + "/for_deploy/", 
                              node_config.working_dir,
                              key = main_config.ssh_key)
    ssh_operations.execOnHost(main_config.ssh_user + "@" + node, 
                              "chmod +x " + "'" + node_config.working_dir + "common/installer.py" + "'",
                              key = main_config.ssh_key)

class NodeTester(paral.Process):
  def __init__(self, node, log_file, first_node = False):
    self.daemon_ready = threading.Lock()
    self.log_file = log_file
    self.dublicate = first_node
    self.status = None
    self.locked = False
    
    paral.Process.__init__(self, 
                           ["ssh"] +
                           ([] if main_config.ssh_key is None else ["-i", main_config.ssh_key]) +
                           [main_config.ssh_user + "@" + node,
                            "python " + node_config.working_dir + "node_tester.py" +
                            (" --deploy-test" if first_node else "")],
                           stdin = subprocess.PIPE,
                           stdout = subprocess.PIPE,
                           stderr = subprocess.STDOUT)
  
  def monitor(self):
    self.daemon_ready.acquire()
    self.locked = True

    try:
      log = open(self.log_file, "w", buffering = 0)
      
      while True:
        line = self.process.stdout.readline()
        if len(line) == 0:
          break
        elif line == "__msg__:node_tester:daemon_prepared\n":
          self.status = "ok"
          self.__daemonIsReady__()
        else:
          if line[-1] == "\n":
            line = line[:-1]
          tester_base.writeLine(line, f = log)
          if self.dublicate:
            tester_base.log(line, "node: ")
    finally:
      self.__daemonIsReady__()
  
  def __daemonIsReady__(self):
    if self.locked:
      self.daemon_ready.release()
      self.locked = False
   
  def start(self):
    paral.Process.start(self)
    self.thread = threading.Thread(target = self.monitor)
    self.thread.start()
  
  def waitForDaemon(self):
    self.daemon_ready.acquire()
  
  def testFinished(self):
    tester_base.writeLine("__msg__:tester:tests_finished", f = self.process.stdin)
        

def testDaemon():
  log_prefix = "testDaemon: "
  
  daemons = []
  for num, node in enumerate(main_config.nodes):
    daemons.append(NodeTester(node, main_config.nodes_dir + str(num) + "/tester.log", first_node = (num == 0)))
  
  tester_base.log("Starting testers on nodes...", log_prefix)
  for d in daemons:
    d.start()
  
  try:
    tester_base.log("Waiting for testers on nodes...", log_prefix)
    
    ok = True
    for d in daemons:
      d.waitForDaemon()
      ok = ok and (d.status == "ok")
    
    if ok:
      tester_base.log("Waiting 5 seconds after starting of daemons...", log_prefix)
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
      tester_base.error("Some node tester has finished with error", log_prefix)
      
  finally:
    tester_base.log("Stopping testers on nodes...", log_prefix)
    for d in daemons:
      d.testFinished()
    for d in daemons:
      d.process.wait()

def downloadFilesFromNodes():
  log_prefix = "downloadFilesFromNodes: "
  tester_base.log("Downloading files (logs, configs, etc) from nodes...", log_prefix)
  
  for num, node in enumerate(main_config.nodes):
    ssh_operations.execOnHost(main_config.ssh_user + "@" + node, 
                              "rm -rf " + "'" + node_config.working_dir + node_config.srv_dir + "'",
                              key = main_config.ssh_key)
    ssh_operations.copyFromHost(main_config.ssh_user + "@" + node,
                                node_config.working_dir,
                                main_config.nodes_dir + str(num),
                                key = main_config.ssh_key)

def installPackages():
  args = []
  for p, v in main_config.packages:
    if v is None:
      args.append(p)
    else:
      args.append(p + "=" + v)
  
  tester_base.execCommand(["sudo", tester_base.script_dir + "common/installer.py"] + args)

def processArgs():
  if len(sys.argv) > 1:
    if sys.argv[1] == "--help":
      print "Usage: main_tester.py [options]"
      print "       main_tester.py --help"
      print "Supported options:"
      print "\t-k or --key <key_file> - file with private key for access to nodes over ssh"
      exit()
    else:
      arg_index = 1
      while arg_index < len(sys.argv):
        if sys.argv[arg_index] == "--key" or sys.argv[arg_index] == "-k":
          main_config.ssh_key = sys.argv[arg_index + 1]
          arg_index += 2
        else:
          print "Unknown option: " + sys.argv[arg_index] + ". Try 'main_tester.py --help'."
          exit()

def main():
  os.putenv("LC_ALL", "C.UTF-8")
  
  processArgs()
  
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
   
  tester_base.log("Success!")

if __name__ == "__main__":
  main()
  