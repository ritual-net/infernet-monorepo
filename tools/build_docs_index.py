import glob
import os

import dominate  # type: ignore
from dominate.tags import a, attr, div, li, link, ol, p, script  # type: ignore

doc = dominate.document(title="Dominate your HTML")

current_directory = os.getcwd()

# Get the list of directories matching the pattern 'docs-*'
docs_directories = glob.glob(os.path.join(current_directory, "docs-*"))
docs = [os.path.basename(directory)[5:] for directory in docs_directories]

print(docs_directories)
with doc.head:
    link(rel="stylesheet", href="style.css")
    script(type="text/javascript", src="script.js")

with doc:
    with div():
        attr(cls="main")
        p("Welcome to the infernet monorepo internal docs index")
    with div(id="toc").add(ol()):
        for i in docs:
            li(a(i.title(), href="/%s/" % i))


# write the doc to a file
with open("index.html", "w") as f:
    f.write(str(doc))
