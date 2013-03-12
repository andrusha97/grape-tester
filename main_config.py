# encoding: utf-8

# IP's of nodes
nodes = []

# packages for installing on main node
packages = [
#           ("package", "version" or None for default version)
            ("elliptics-client", "2.21.4.3")
            ]

log_file = "tester.log"

ssh_user = "bugsbunny" # user on nodes
ssh_key = "key.rsa" # key for access to nodes

elliptics_conf = "templates/elliptics.conf.tmpl"
cocaine_conf = "templates/cocaine.conf.tmpl"
test_manifest = "templates/manifest.json.tmpl"
test_profile = "templates/profile.json.tmpl"
test_cpp = "templates/test.cpp.tmpl"

nodes_dir = "nodes/"