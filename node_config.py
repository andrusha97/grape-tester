# encoding: utf-8

# general parameters
working_dir = "/home/bugsbunny/grape-tester-node/"

# port through which node tester will communicate with main tester
port = 31337

# packages to install on nodes
packages = [
#           ("package", "version" or None for default version)
            ("elliptics-client", "2.21.4.3"),
            ("elliptics", "2.21.4.3"),
            ("elliptics-dev", "2.21.4.3"),
            ("libcocaine-core2", "0.10.0-rc4"),
            ("cocaine-worker-generic", "0.10.0-rc3"),
            ("libcocaine-plugin-binary", "0.10.0-rc2"),
            ("libcocaine-plugin-elliptics", "0.10.0-rc2"),
            ("grape", "0.5.3"),
            ("cocaine-tools", "0.10.0-rc4"),
            ("libzmq3", "3.2.4+yandex1"),
            ("libboost-all-dev", "1.48.0.2")
            ]

# paths to configs in node_files/
elliptics_conf = "conf/elliptics.conf"
cocaine_conf = "conf/cocaine.conf"

# path to directory with test application in node_files/
build_dir = "test_app/"

# some files in build_dir
# *.so and *.tar will be made by script
# manifest and profile must be in the directory with configuration of nodes (in node_files/<build_dir>/)
soname = "libetest.so"
tar_name = "etest.tar"
manifest = "manifest.json"
profile = "profile.json"