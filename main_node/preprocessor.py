# encoding: utf-8

def applySubstitutions(string, subst_list):
  res = string
  for p, s in subst_list:
    res = res.replace(p, s)
  return res

def processFile(infile, outfile, subst_list):
  f1 = open(infile, "r")
  f2 = open(outfile, "w")
  f2.write(applySubstitutions(f1.read(), subst_list))
