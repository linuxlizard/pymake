# https://perfectmotherfuckingwebsite.com/
# copyrighted https://creativecommons.org/publicdomain/zero/1.0/
#
css = """
body{max-width:650px;margin:40px auto;padding:0 10px;font:18px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";color:#444}h1,h2,h3{line-height:1.2}@media (prefers-color-scheme: dark){body{color:#c9d1d9;background:#0d1117}a:link{color:#58a6ff}a:visited{color:#8e96f0}}
"""

top="""
<!DOCTYPE html>
<html lang="en"><head>
<meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <meta charset="utf-8">
    <title>Makefile</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="">
    <link rel="stylesheet" href="style.css">
    <link rel="icon" href="data:image/svg+xml,&lt;svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22&gt;&lt;text y=%22.9em%22 font-size=%2290%22&gt;%F0%9F%96%95&lt;/text&gt;&lt;/svg&gt;">
  </head>
  <body>
"""

bottom="""
</body></html>
"""

def p(s):
    return "<p>%s</p>\n" % s

def _save_rules(outfile, rules):
    for target,rule in rules.items():
        outfile.write(p(target + " : " + " ".join([pr for pr in rule.prereq_list if not pr.startswith("/usr")])))

def save_rules(outfilename, rules):
    with open("style.css","w") as outfile:
        outfile.write(css)

    with open(outfilename,"w") as outfile:
        outfile.write(top)
        _save_rules(outfile,rules)
        outfile.write(bottom)

