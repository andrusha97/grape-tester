#!/usr/bin/python
# encoding: utf-8

from common import tester_base, paral
import node_config
import time, sys, os, subprocess, threading, argparse


def buildTestApp():
  log_prefix = "buildTestApp: "

  tester_base.log("Building test grape application...", log_prefix)

  compile_cmd = ['c++', '-fPIC', '-std=c++0x',
                 '-o', 'etest.o', '-c', node_config.cpp_name]
  link_cmd = ['c++', '-fPIC', '-shared', '-Wl,-soname,' + node_config.soname, 
              '-o', node_config.soname, 'etest.o', '/usr/lib/libgrape.so', 
              '-lelliptics', '-lelliptics_cpp', '-leblob', 
              '-lboost_system-mt', '-lboost_thread-mt', '-lgrapejson']
  tar_cmd = ['tar', '-cf', node_config.tar_name, node_config.soname]

  old_cwd = os.getcwd()
  os.chdir(node_config.build_dir)
  
  tester_base.log("Compiling test application...", log_prefix)
  tester_base.execCommand(compile_cmd)

  tester_base.log("Linking module...", log_prefix)
  tester_base.execCommand(link_cmd)

  tester_base.log("Making application archive...", log_prefix)
  tester_base.execCommand(tar_cmd)

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
  os.chdir(node_config.build_dir)   

  uploadApp(os.path.join(node_config.working_dir, node_config.cocaine_conf), node_config.manifest, 
            node_config.profile, node_config.tar_name, "test-app")
  uploadApp(os.path.join(node_config.working_dir, node_config.cocaine_conf), node_config.manifest,
            node_config.profile, node_config.tar_name, "test-app-second")
  
  os.chdir(old_cwd)

DAEMON_FAILED = 1
SUCCESSFUL_TEST = 2

# result is list with one item
# if result[0] is None then function must write into result[0] self unique id
def runElliptics(lock, process, result):
  log_prefix = "runElliptics: "

  tester_base.log("Starting elliptics daemon...", log_prefix)
  process.start()
  process.wait()
  
  with lock:
    tester_base.log("Daemon stoped", log_prefix)
    
    if result[0] is None:
      result[0] = DAEMON_FAILED

def testElliptics(lock, process, result):
  log_prefix = "testElliptics: "
  
  try:
    tester_base.log("Waiting 5 seconds for starting of daemon...", log_prefix)
    time.sleep(5)
    
    if process.poll() is not None:
      return
    
    if node_config.deploy_test:
      tester_base.log("Deploing test applications...", log_prefix)
      uploadTestApp()
    
    tester_base.log("Elliptics is ready", log_prefix)
    tester_base.writeLine("__msg__:node_tester:daemon_prepared")
  
    tester_base.log("Waiting for ending of test...", log_prefix)
    while tester_base.readLine() != "__msg__:tester:tests_finished" and process.poll() is None:
      pass
  
    with lock:
      if process.poll() is None and result[0] is None:
        result[0] = SUCCESSFUL_TEST
  finally:
    if process.poll() is None:
      tester_base.log("Killing daemon...", log_prefix)
      process.kill()

def installPackages():
  args = []
  for p, v in node_config.packages:
    if v is None:
      args.append(p)
    else:
      args.append(p + "=" + v)
  
  tester_base.execCommand(["sudo", os.path.join(node_config.working_dir, "common/installer.py")] + args)

def processArgs():
  parser = argparse.ArgumentParser()
  parser.add_argument("packages", nargs = "*", help = "packages to install")
  parser.add_argument("--deploy-test",
                      action = "store_true",
                      default = node_config.deploy_test,
                      help = "build and deploy test application in elliptics")
  args = parser.parse_args()
  
  node_config.deploy_test = args.deploy_test
  
  for p in args.packages:
    parts = p.split('=')
    if len(parts) > 1:
      node_config.packages.append((parts[0], parts[1]))
    else:
      node_config.packages.append((parts[0], None))

def main():
  processArgs()
  os.chdir(node_config.working_dir)

  installPackages()
  
  if node_config.deploy_test:
    buildTestApp()
  
  # run elliptics and test it
  p = paral.Process(["dnet_ioserv", "-c", node_config.elliptics_conf])
  result = [None]
  
  lock = threading.Lock()
  perf = paral.MultiTaskPerformer([runElliptics, testElliptics], (lock, p, result))
  perf.start()
  perf.joinAll()
  p.wait()

  tester_base.log("Test is finished")
  if result[0] == SUCCESSFUL_TEST:
    tester_base.log("Everything works")
  elif result[0] == DAEMON_FAILED:
    tester_base.log("Daemon failed")
  else:
    tester_base.error("Unexpected result of testing. Something is wrong.")

#########################################################################
if __name__ == "__main__":
  main()
