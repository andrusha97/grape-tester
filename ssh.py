# encoding: utf-8

import os, stat

def sftpExists(sftp, file):
  try:
    sftp.lstat(file)
    return True
  except IOError:
    return False

def sftpCopyFromRemote(sftp, src, dest):
  if sftpExists(sftp, src):
    attr = sftp.stat(src)
    if stat.S_ISDIR(attr.st_mode):
      os.mkdir(dest)
      for file in sftp.listdir(src):
        sftpCopyFromRemote(sftp, os.path.join(src, file), os.path.join(dest, file))
    elif stat.S_ISREG(attr.st_mode):
      sftp.get(src, dest)

def sftpCopyToRemote(sftp, src, dest):
  attr = os.stat(src)
  if stat.S_ISDIR(attr.st_mode):
    sftp.mkdir(dest)
    for file in os.listdir(src):
      sftpCopyToRemote(sftp, os.path.join(src, file), os.path.join(dest, file))
  elif stat.S_ISREG(attr.st_mode):
    sftp.put(src, dest)

def sftpRemove(sftp, file):
  if sftpExists(sftp, file):
    attr = sftp.stat(file)
    if stat.S_ISDIR(attr.st_mode):
      for f in sftp.listdir(file):
        sftpRemove(sftp, os.path.join(file, f))
      sftp.rmdir(file)
    elif stat.S_ISREG(attr.st_mode):
      sftp.remove(file)