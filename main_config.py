# encoding: utf-8

import sys as _sys_, os as _os_
  
_script_dir_ = _os_.path.abspath(_os_.path.dirname(_sys_.argv[0]))
  
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

# file with key for access to nodes
# may be overridden with --key parameter
# if None then key will not be used
ssh_key = None

elliptics_conf = _os_.path.join(_script_dir_, "templates/elliptics.conf.tmpl")
cocaine_conf = _os_.path.join(_script_dir_, "templates/cocaine.conf.tmpl")
test_manifest = _os_.path.join(_script_dir_, "templates/manifest.json.tmpl")
test_profile = _os_.path.join(_script_dir_, "templates/profile.json.tmpl")
test_cpp = _os_.path.join(_script_dir_, "templates/test.cpp.tmpl")
