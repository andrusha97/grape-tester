# encoding: utf-8

import sys as _sys_, os as _os_
  
_script_dir_ = _os_.path.abspath(_os_.path.dirname(_sys_.argv[0]))
if _script_dir_[-1] != "/":
  _script_dir_ += "/"
  
# IP's of nodes
nodes = []

# packages for installing on main node
packages = [
#           ("package", "version" or None for default version)
            ("elliptics-client", "2.21.4.3")
            ]

log_file = "tester.log"

# directory for files from nodes (e.g. logs)
nodes_dir = "nodes/"

# user on nodes
ssh_user = "bugsbunny"

# key for access to nodes
# may be overridden with --key parameter
ssh_key = _script_dir_ + "key.rsa"

elliptics_conf = _script_dir_ + "templates/elliptics.conf.tmpl"
cocaine_conf = _script_dir_ + "templates/cocaine.conf.tmpl"
test_manifest = _script_dir_ + "templates/manifest.json.tmpl"
test_profile = _script_dir_ + "templates/profile.json.tmpl"
test_cpp = _script_dir_ + "templates/test.cpp.tmpl"
