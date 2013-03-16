#!/usr/bin/python
# encoding: utf-8

import apt, tester_base, optparse, signal, logging

# packages is list of pairs (package: str, version: str)
# if version is None then default candidate will be installed
def installPackages(packages):
  logging.info("Following packages will be installed: " +
              ", ".join([p + "=" + str(v) for p, v in packages]))

  c = apt.Cache()
  try:
    logging.info("Updating the cache...")
    c.update(raise_on_error = False)
    c.open()
    for pack, ver in packages:
      p = c[pack]
      if ver:
        p.candidate = p.versions[ver]
      p.mark_install()
    
    logging.info("Commit changes...")
    if not c.commit():
      tester_base.error("Unable to commit changes")
  except KeyError as e:
    tester_base.error(repr(e))

if __name__ == '__main__':
  signal.signal(signal.SIGINT, signal.SIG_IGN)
  logging.basicConfig(level = logging.INFO, format = "installer: %(message)s")
  
  parser = optparse.OptionParser(usage = "Usage: %prog [options] packages")
  (options, args) = parser.parse_args()
  
  packages = []
  
  for p in args:
    parts = p.split('=')
    if len(parts) > 1:
      packages.append((parts[0], parts[1]))
    else:
      packages.append((parts[0], None))

  installPackages(packages)
