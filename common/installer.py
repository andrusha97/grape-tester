#!/usr/bin/python
# encoding: utf-8

import sys, apt, tester_base

# packages is list of pairs (package: str, version: str)
# if version is None then default candidate will be installed
def installPackages(packages):
  log_prefix = "installPackages: "
  tester_base.log("Following packages will be installed: " + \
                   ", ".join([p + "=" + str(v) for p, v in packages]), 
                   log_prefix)

  c = apt.Cache()
  try:
    tester_base.log("Updating the cache...", log_prefix)
    c.update(raise_on_error = False)
    c.open()
    for pack, ver in packages:
      p = c[pack]
      if ver:
        p.candidate = p.versions[ver]
      p.mark_install()
    
    tester_base.log("Commit changes...", log_prefix)
    if not c.commit():
      tester_base.error("Unable to commit changes", log_prefix)
  except KeyError as e:
    tester_base.error(repr(e), log_prefix)
  except apt.cache.FetchFailedException as e:
    tester_base.error(repr(e), log_prefix)
  except apt.cache.LockFailedException as e:
    tester_base.error(repr(e), log_prefix)
  except apt.cache.FetchCancelledException as e:
    tester_base.error(repr(e), log_prefix)

if __name__ == '__main__':
  packages = []

  for p in sys.argv[1:]:
    parts = p.split('=')
    if len(parts) > 1:
      packages.append((parts[0], parts[1]))
    else:
      packages.append((parts[0], None))

  installPackages(packages)
