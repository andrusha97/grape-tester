#!/usr/bin/python
# encoding: utf-8

from common import tester_base, installer
import ssh
import main_config, node_config
import os, shutil, threading, subprocess, time, optparse, re, socket, logging, paramiko

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

class NodeDealer:
  def __init__(self, node, id, show_log = False):
    self.node = node
    self.id = id
    self.show_log = show_log
    
    self.messenger = None
    self.monitor = None
    
    self.ssh_client = paramiko.SSHClient()
    self.ssh_client.load_system_host_keys()
    self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    self.ssh_client.connect(node,
                            username = main_config.ssh_user,
                            key_filename = main_config.ssh_key)
    self.sftp_client = self.ssh_client.open_sftp()
  
  def start(self):
    tester_cmd = "'%s'" % os.path.join(node_config.working_dir, "node_tester.py")
    streams = self.ssh_client.exec_command(tester_cmd, bufsize = 0)
    
    self.monitor = threading.Thread(target = self.monitorTester_, args = (streams[1],))
    self.monitor.daemon = True
    self.monitor.start()
    
    self.connect_()
  
  def wait(self):
    if self.monitor is not None:
      self.monitor.join()
  
  def connect_(self):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    address = (self.node, node_config.port)
    
    logging.info("Connecting to node %s:%d..." % address)
    for x in xrange(3):
      try:
        s.connect(address)
        break;
      except socket.error:
        pass
      time.sleep(3)
    else:
      tester_base.error("Can't establish connection to node %s:%d..." % address)
      
    self.messenger = s.makefile("w+", bufsize = 1)
  
  def monitorTester_(self, stdout):
    while True:
      line = stdout.readline()
      if len(line) == 0:
        break
      elif self.show_log:
        logging.info(self.node + ": " + line.rstrip("\n"))
  
  def messengerState(self):
    if self.messenger is None:
      return "not connected"
    elif self.messenger.closed:
      return "closed"
    else:
      return "active"
  
  def readMessage(self):
    if self.messengerState() == "active":
      try:
        line = self.messenger.readline()
        if len(line) > 0:
          return line.rstrip("\n")
      except socket.error:
        pass
      
    return None
  
  def writeMessage(self, line):
    if self.messengerState() == "active":
      try:
        print >> self.messenger, line
      except socket.error:
        pass
  
  def execCommand(self, msg):
    self.writeMessage(msg)
    if self.readMessage() != "msg:ok":
      tester_base.error("Error has occured on node %s. "
                        "Try to see on logs in '%s' to investigate the problem." %
                        (self.node, os.path.join(main_config.nodes_dir, str(self.id))))
  
  def finish(self):
    if self.messengerState() == "active":
      self.messenger.close()
  
  def prepareFiles(self):
    for_deploy = os.path.join(main_config.nodes_dir, str(self.id), "to_deploy/")
    os.makedirs(for_deploy)
    
    shutil.copytree(main_config.node_files,
                    os.path.join(for_deploy, tester_base.files_on_node))
    
    preprocessDirectory(os.path.join(for_deploy, tester_base.files_on_node),
                        {
                          "node_config": node_config,
                          "main_config": main_config,
                          "node": self.node,
                          "node_id": self.id
                        })
    
    shutil.copytree(os.path.join(tester_base.script_dir, "common/"),
                    os.path.join(for_deploy, "common/"))
    shutil.copy(os.path.join(tester_base.script_dir, "node_config.py"), for_deploy)
    shutil.copy(os.path.join(tester_base.script_dir, "node_tester.py"), for_deploy)
    
    logging.info("Node tester has been written to '%s'." % for_deploy)
  
  def uploadTester(self):
    for_deploy = os.path.join(main_config.nodes_dir, str(self.id), "to_deploy/")
    ssh.sftpRemove(self.sftp_client, node_config.working_dir, ignore_errors = True)
    ssh.sftpCopyToRemote(self.sftp_client, for_deploy, node_config.working_dir)
    self.sftp_client.chmod(os.path.join(node_config.working_dir, "node_tester.py"), 0755)
    self.sftp_client.chmod(os.path.join(node_config.working_dir, "common/installer.py"), 0755)
  
  def downloadFiles(self):
    for f in main_config.remove_before_downloading:
      ssh.sftpRemove(self.sftp_client,
                     os.path.join(node_config.working_dir, f),
                     ignore_errors = True)
    
    ssh.sftpCopyFromRemote(self.sftp_client,
                           os.path.join(node_config.working_dir, tester_base.files_on_node),
                           os.path.join(main_config.nodes_dir, str(self.id), tester_base.files_on_node))
    ssh.sftpCopyFromRemote(self.sftp_client,
                           os.path.join(node_config.working_dir, "tester.log"),
                           os.path.join(main_config.nodes_dir, str(self.id), "tester.log"))
  
  def killOld(self):
    self.ssh_client.exec_command("killall node_tester.py")
    self.ssh_client.exec_command("killall dnet_ioserv")

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

def testElliptics(dealers):  
  logging.info("Run elliptics daemons. It may take some time (about 10 seconds per node).")
  for d in dealers:
    d.execCommand("msg:run_elliptics")
  
  logging.info("Uploading test application...")
  dealers[0].execCommand("msg:upload_app")
  
  testApplication()
  
  for d in dealers:
    d.writeMessage("msg:check_daemon")
    if d.readMessage() != "msg:works":
      tester_base.error("Elliptics daemon unexpectedly finished on node %s. "
                        "Try to see on logs in '%s' to investigate the problem." %
                        (d.node, os.path.join(main_config.nodes_dir, str(d.id))))
  
  logging.info("Waiting for finishing of elliptics daemons...")
  for d in dealers:
    d.execCommand("msg:kill_daemon")
  
  for d in dealers:
    d.execCommand("msg:wait_daemon")
    
  for d in dealers:
    d.writeMessage("msg:bye")  

def installPackages():
  tester_base.execCommand(["sudo", os.path.join(tester_base.script_dir, "common/installer.py")] +
                          [p if v is None else p + "=" + v for p, v in main_config.packages])
def performTest():
  installPackages()
  
  dealers = [NodeDealer(node, num, show_log = (num == 0))
             for num, node in enumerate(main_config.nodes)]
  
  if main_config.killold:
    for d in dealers:
      d.killOld()
  
  logging.info("Preparing tester for uploading to nodes...")
  shutil.rmtree(main_config.nodes_dir, ignore_errors = True)
  for d in dealers:
    d.prepareFiles()
  
  logging.info("Uploading tester to nodes...")
  for d in dealers:
    d.uploadTester()
  
  try:
    logging.info("Start testers on nodes nodes...")
    for d in dealers:
      d.start()
    
    try:
      for d in dealers:
        d.execCommand("msg:install_packages")
      
      dealers[0].execCommand("msg:build_app")
      
      testElliptics(dealers)
    finally:
      logging.info("Downloading files (logs, configs, etc) from nodes. "
                   "These files may help you if something was wrong.")
      for d in dealers:
        d.downloadFiles()
      logging.info("You can find these files in '%s', "
                   "logs of node testers in '%s', "
                   "log of this script in '%s'." %
                   (os.path.join(main_config.nodes_dir, "{0, 1, ...}", tester_base.files_on_node),
                    os.path.join(main_config.nodes_dir, "{0, 1, ...}", "tester.log"),
                    main_config.log_file))
  finally:
    logging.info("Waiting for finishing of node testers...")
    for d in dealers:
      d.finish()
    for d in dealers:
      d.wait()
  
  logging.info("Success!")

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
    performTest()
  
################################################################################
if __name__ == "__main__":
  main()
  