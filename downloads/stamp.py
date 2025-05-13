import os, glob, re, shutil, webbrowser
from git import Repo
from datetime import date

dst = 'active-build'
src = 'desat/'
tempDirectory = 'scraps'
allowList = '.git'
headerFile = 'templates/header.html'
footerFile = 'templates/footer.html'
title = "title"
liveBuild = False
syndicateEverywhere = False

def insertText(rawText, breakText, insertText, beforeToggle):
    t = rawText.split(breakText, 1)
    return t[0] + insertText * beforeToggle + breakText + insertText * (not beforeToggle) + t[1]

def saturater(dst, headerFile, footerFile, titleText):
    #import template files
    header = open(headerFile).read()
    footer = open(footerFile).read()
    #for each html file in directory 'dst'
    for filename in glob.glob(os.path.join(dst, '**/*.html'), recursive = True):
        with open(os.path.join(os.getcwd(), filename), 'r') as f:
            # if file has manual head, do not saturate
            print(filename)
            f.seek(0)
            if re.search(r'<head>',f.read()) != None:
                print('manual html head skipping:' + filename + "\n")
                continue
            #extract article title
            f.seek(0)
            splitFile = re.split('<h1.*?>', f.read(), 1)
            f.seek(0)
            splitFile = splitFile + re.split('</h1>', splitFile[1], 1)
            splitFile.pop(1)
            title = splitFile[1]
            output = splitFile[0] + "<h1>" + title + "</h1>" + splitFile[2]
            #add header and footer templates
            output = header + output + footer
            #if second level of new tree, make header base on parent dir
            if len(filename.replace(dst, '').split('/')) == 2:
                output = output.replace('<base href = ".">', '<base href = "..">')
            #replace title placeholder with extracted title and title template
            #this is inefficent. Just change the one article
            if filename.split('/')[-1] == 'index.html':
                output = output.replace("<!--TITLE-->", titleText)
            else:
                output = output.replace("<!--TITLE-->", title + ", " + titleText)
            open(filename, 'w').write(output)

def insertBlogPosts (dst, postCount):
    articlesPath = 'desat/articles/'
    blogAppendFile = dst + "index.html"
    blogLength = postCount
    #get all file paths in a list
    paths = glob.glob(os.path.join(articlesPath, '*.html'))
    #get all file dates and store them with the paths (dictionary?)
    pathAndDate = {}
    for filename in paths:
        with open(filename) as f:
            dateExtracted = re.search(r"<time datetime=.(?P<date>.*?).>", f.read())['date']
            dateExtracted = date.fromisoformat(dateExtracted)
            pathAndDate.update({filename: dateExtracted})
        f.close()
    #create list of paths sorted reverse chronological
    pathAndDate = sorted(pathAndDate, key=pathAndDate.get)
    pathAndDate.reverse()
    #trim list of paths (by how many wanted for scroll)
    del pathAndDate[blogLength:]
    cleanedPaths = pathAndDate
    #append all the file contents of the paths
    text = ''
    for filename in cleanedPaths:
        with open(filename, 'r') as f:
            f.seek(0)
            text = text + '\n<hr>\n' + f.read()
        f.close()
    #clean up the headers (h1 -> h2 etc.)
    text = text.replace('h5', 'h6')
    text = text.replace('h4', 'h5')
    text = text.replace('h3', 'h4')
    text = text.replace('h2', 'h3')
    text = text.replace('h1', 'h2')
    #add blog heading to the beguining
    text = open('desat/index.html').read() + text
    #add link to archive at the end
    text = text + "\n\n<p><a href='archive.html'>more</a></p>"
    #write to file
    open(blogAppendFile, 'w').write(text)

def syndicate(directory):
    fileToPush = input("Select post to publish: ") + '.html'
    rss = 'desat/rss.xml'
    url = 'https://www.haydenshuker.com/'+ fileToPush
    archive = 'desat/archive.html'
    ##LOAD FILES
    #extract and write title. Use a regular expression to find it burried in h1
    f = open(directory + fileToPush)
    title = re.search(r"<h1.*?>(?P<title>.*?)</h1>", f.read())['title']
    f.close()
    #post to RSS
    rssAppendText = '\n<item>\n<title>' + title + '</title>\n '+ '<link>' + url + '</link>\n</item>\n'
    rssText = insertText(open(rss).read(),'</channel>', rssAppendText, True)
    print(rssText)
    if input("save new rss Text? y/N") == "y":
        open(rss, "w").write(rssText)
    ##archive it
    archiveCatagory = input("archive catagory (usualy the year, must exist in archive file already): ")
    archiveAppendText = '\n<li><a href=\'' + fileToPush + '\'>' + title +'</a></li>'
    archiveText = insertText(open(archive).read(), '<h2>' + archiveCatagory+ '</h2>\n<ul>', archiveAppendText, False)
    print(archiveText)
    if input("save new archive Text? y/N") == "y":
        open(archive, "w").write(archiveText)

def gitPush(repo_src):
    repo = Repo(repo_src)
    repo.git.add(all=True)
    repo.index.commit("stamp push")
    origin = repo.remote(name='origin')
    origin.push()

def buildSite(live, syndicate):
    ## pre saturation, happens in desat folder
    if syndicate:
        syndicate(src)
    ##COPY DIR
    #move whitelist dir asside
    try:
        shutil.copytree(dst + allowList, tempDirectory)
    except:
        print("no .git folder")
    #remove and replace dst
    shutil.rmtree(dst)
    shutil.copytree(src, dst)
    insertBlogPosts(dst, 3)
    #put whitlist back in
    try:
        shutil.copytree(tempDirectory, dst + allowList)
        shutil.rmtree(tempDirectory)
    except:
        print("no temp dir")
    saturater(dst, headerFile, footerFile, title)
    if(live):
        gitPush(dst)

## script
if input("push to public? y/N")=="y":
    liveBuild = True
if input("syndicate post? y/N")=="y":
    syndicateEverywhere = True
if input("open local? y/N")=="y":
    webbrowser.open(dst+'index.html')

buildSite(liveBuild, syndicateEverywhere)
