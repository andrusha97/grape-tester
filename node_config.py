# encoding: utf-8

# general parameters
working_dir = "/home/bugsbunny/grape-tester-node/"
elliptics_conf = "conf/elliptics.conf"
cocaine_conf = "conf/cocaine.conf"
logs_dir = "logs/"
leveldb_dir = "leveldb/"
history_dir = "history/"
srv_dir = "srv/" # for run, spool, cache, etc

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

# build and upload test application
deploy_test = False
build_dir = "test_app/"
cpp_name = "test.cpp"
soname = "libetest.so"
tar_name = "etest.tar"
manifest = "manifest.json"
profile = "profile-single.json"



