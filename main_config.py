# encoding: utf-8

import sys as _sys_, os as _os_
_script_dir_ = _os_.path.abspath(_os_.path.dirname(_sys_.argv[0]))
  
# IP's of nodes
nodes = ["5.45.241.103"]

# packages for installing on main node
packages = [
#           ("package", "version" or None for default version)
            ("elliptics-client", "2.21.4.3")
            ]

log_file = "tester.log"

# directory for files from nodes (e.g. logs)
nodes_dir = "nodes/"

# directory with nodes configuration
# all files with .tmpl extension in this directory will be preprocessed for each node
# and then the directory will be copied to the node
node_files = _os_.path.join(_script_dir_, "node_files/")

# some files must be removed before coping of working directory from node (e.g. sockets)
remove_before_downloading = ["files/var/run/cocaine/engines/"]

# user on nodes
ssh_user = "bugsbunny"

# file with key for access to nodes
# may be overridden with --key parameter
# if None then key will not be used
ssh_key = None