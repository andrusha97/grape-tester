#!/usr/bin/python
# encoding: utf-8

from common import tester_base, installer, paral
import ssh
import main_config, node_config
import os, shutil, threading, subprocess, time, optparse, re, socket, logging

class NodeDealer:
  def __init__(self, node, first_node = False):
    self.node = node
    
    self.socket = None
    self.reader = None
    self.writer = None
    self.connection_state = "not connected"
    
    if first_node:
      self.logger = threading.Thread(target = self.log)
      self.logger.daemon = True
      
      userhost = main_config.ssh_user + "@" + node
      key = [] if main_config.ssh_key is None else ["-i", main_config.ssh_key]
      tester_cmd = "'%s' --deploy-test" % os.path.join(node_config.working_dir, "node_tester.py")
      
      self.process = paral.Process(["ssh"] + key + [userhost, tester_cmd],
                                   stdin = subprocess.PIPE,
                                   stdout = subprocess.PIPE,
                                   stderr = subprocess.STDOUT)
    else:
      self.logger = None
      
      userhost = main_config.ssh_user + "@" + node
      key = [] if main_config.ssh_key is None else ["-i", main_config.ssh_key]
      tester_cmd = "'%s'" % os.path.join(node_config.working_dir, "node_tester.py")
      
      self.process = paral.Process(["ssh"] + key + [userhost, tester_cmd],
                                   stdin = open("/dev/null", "r"),
                                   stdout = open("/dev/null", "w"),
                                   stderr = open("/dev/null", 'w'))
  
  def log(self):
    while True:
      line = self.process.process.stdout.readline()
      if len(line) > 0:
        logging.info(self.node + ": " + line.rstrip("\n"))
      else:
        break;
  
  def start(self):
    self.process.start()
    if self.logger is not None:
      self.logger.start()
    
    self.connect_()
  
  def connect_(self):
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    address = (self.node, node_config.port)
    
    logging.info("Connecting to node %s:%d..." % address)
    for x in xrange(3):
      try:
        self.socket.connect(address)
        break;
      except socket.error:
        pass
      time.sleep(3)
    else:
      tester_base.error("Can't establish connection to node %s:%d..." % address)
      
    self.reader = self.socket.makefile("r", bufsize = 0)
    self.writer = self.socket.makefile("w", bufsize = 0)
    self.connection_state = "connected"
  
  def readLine(self):
    if self.connection_state == "connected":
      line = self.reader.readline()
      return line.rstrip("\n") if len(line) > 0 else None
    else:
      return None
  
  def writeLine(self, line):
    if self.connection_state == "connected":
      print >> self.writer, line
  
  def finish(self):
    if self.connection_state == "connected":
      self.writer.close()
      self.reader.close()
      self.socket.close()
      self.connection_state = "disconnected"
  
  def wait(self):
    if self.process.isStarted():
      self.process.wait()
    if self.logger is not None:
      self.logger.join()
        
def testApplication():
  logging.info("Launching test application...")
  
  tester_base.execCommand(("dnet_ioclient -r " + main_config.nodes[0] + ":1025:2 -g2 -c test-app@start-task").split())
  tester_base.execCommand(("dnet_ioclient -r " + main_config.nodes[0] + ":1025:2 -g2 -c test-app-second@start-task").split())
  
  output = subprocess.check_output(("dnet_ioclient -r " + main_config.nodes[0] + ":1025:2 -g2 -c").split() + ["test-app@event0 xxx"])
  
  tester_base.execCommand(("dnet_ioclient -r " + main_config.nodes[0] + ":1025:2 -g2 -c test-app-second@stop-task").split())
  tester_base.execCommand(("dnet_ioclient -r " + main_config.nodes[0] + ":1025:2 -g2 -c test-app@stop-task").split())
  
  if output != "xxx123test-app-second@event0|test-app-second@event1|test-app-second@event2|test-app-second@finish|":
    tester_base.error("dnet_ioclient returned string '" + output + "'. Something is wrong.", log_prefix)
  else:
    logging.info("Test has been successfully completed.")

def testElliptics():
  dealers = [NodeDealer(node, first_node = (num == 0))
             for num, node in enumerate(main_config.nodes)]
  
  try:
    logging.info("Starting testers on nodes...")
    for d in reversed(dealers):
      d.start()
      
    logging.info("Waiting for testers on nodes...")
    
    fail = [n for n, d in enumerate(dealers) if d.readLine() != "msg:daemon_prepared"]
    
    if len(fail) == 0:
      logging.info("Waiting 5 seconds after starting of daemons...")
      time.sleep(5)
      
      dealers[0].writeLine("msg:upload_app")
      
      if dealers[0].readLine() != "msg:application_uploaded":
        tester_base.error("Application has not been uploaded.")
      
      logging.info("Waiting 5 seconds after uploading of application...")
      time.sleep(5)
      
      testApplication()
        
    else:
      tester_base.error("Following node testers finished with error: " +
                        ', '.join([str(n) for n in fail]))
      
  finally:
    logging.info("Stopping testers on nodes...")
    for d in dealers:
      d.finish()
    for d in dealers:
      d.wait()

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
  logging.info("Preparing tester for uploading to nodes...")
  
  shutil.rmtree(main_config.nodes_dir, ignore_errors = True)
  
  # create folders for files (scripts, logs, etc) from nodes: nodes/0/, nodes/1/, ...
  for dname, node in enumerate(main_config.nodes):
    for_deploy = os.path.join(main_config.nodes_dir, str(dname), "to_deploy/")
    os.makedirs(for_deploy)
    
    shutil.copytree(main_config.node_files,
                    os.path.join(for_deploy, tester_base.files_on_node))
    
    preprocessDirectory(os.path.join(for_deploy, tester_base.files_on_node),
                        {
                          "node_config": node_config,
                          "main_config": main_config,
                          "node": node
                        })
    
    shutil.copytree(os.path.join(tester_base.script_dir, "common/"),
                    os.path.join(for_deploy, "common/"))
    shutil.copy(os.path.join(tester_base.script_dir, "node_config.py"), for_deploy)
    shutil.copy(os.path.join(tester_base.script_dir, "node_tester.py"), for_deploy)
    
    logging.info("Node tester has been written to '%s'." % for_deploy)

def uploadTesterToNodes():
  logging.info("Uploading tester to nodes...")
  
  for num, node in enumerate(main_config.nodes):
    dealer = ssh.SSHDealer(main_config.ssh_user, node, main_config.ssh_key)
    
    dealer.execute("rm -rf " + "'" + node_config.working_dir + "'")
    dealer.copyTo(os.path.join(main_config.nodes_dir, str(num), "to_deploy/"),
                  node_config.working_dir)
    dealer.execute("chmod +x '%s'" % os.path.join(node_config.working_dir, "common/installer.py"))
    dealer.execute("chmod +x '%s'" % os.path.join(node_config.working_dir, "node_tester.py"))

def downloadFilesFromNodes():
  logging.info("Downloading working directories (with logs, configs, etc) from nodes...")
  
  for num, node in enumerate(main_config.nodes):
    dealer = ssh.SSHDealer(main_config.ssh_user, node, main_config.ssh_key)
    
    for f in main_config.remove_before_downloading:
      dealer.execute("rm -rf '%s'" % os.path.join(node_config.working_dir, f))
    
    dealer.copyFrom(os.path.join(node_config.working_dir, tester_base.files_on_node),
                    os.path.join(main_config.nodes_dir, str(num)))
    dealer.copyFrom(os.path.join(node_config.working_dir, "tester.log"),
                    os.path.join(main_config.nodes_dir, str(num)))

def installPackages():
  tester_base.execCommand(["sudo", os.path.join(tester_base.script_dir, "common/installer.py")] +
                          [p if v is None else p + "=" + v for p, v in main_config.packages])

def performTest():
  installPackages()
  prepareFilesForNodes()
  uploadTesterToNodes()
  try:
    testElliptics()
  finally:
    downloadFilesFromNodes()
    logging.info("You can find files from nodes in '%s', "
                 "logs of node testers in '%s', "
                 "log of this script in '%s'." %
                 (os.path.join(main_config.nodes_dir, "{0, 1, ...}", tester_base.files_on_node),
                  os.path.join(main_config.nodes_dir, "{0, 1, ...}", "tester.log"),
                  main_config.log_file))
  
  logging.info("Success!")

def killOldTesters():
  for node in main_config.nodes:
    d = ssh.SSHDealer(main_config.ssh_user, node, main_config.ssh_key)
    d.execute("killall node_tester.py", raise_on_error = False)
    d.execute("killall dnet_ioserv", raise_on_error = False)

def processArgs():
  parser = optparse.OptionParser()
  parser.add_option("-k",
                    "--key",
                    default = main_config.ssh_key,
                    help = "file with private key for access to nodes over ssh")
  parser.add_option("--kill-old",
                    action = "store_true",
                    help = "kill old copies of elliptics and node_tester.py on nodes")
  (options, args) = parser.parse_args()
  main_config.ssh_key = options.key
  main_config.killold = options.kill_old

def main():
  os.putenv("LC_ALL", "C.UTF-8")
  processArgs()
  
  if len(main_config.nodes) == 0:
    print "List of nodes in main_config.py is empty."
  else:
    tester_base.setupLogging(main_config.log_file)
    if main_config.killold:
      killOldTesters()
    performTest()
  
################################################################################
if __name__ == "__main__":
  main()
  