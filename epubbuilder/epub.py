# -*- coding: utf-8 -*-

# Copyright (c) 2012, Bin Tan
# This file is distributed under the BSD Licence.
# See python-epub-builder-license.txt for details.

import itertools
import mimetypes
import os
import shutil
import subprocess
import uuid
import zipfile
from genshi.template import TemplateLoader
from lxml import etree


class TocMapNode:
    def __init__(self):
        self.playOrder = 0
        self.title = ''
        self.href = ''
        self.children = []
        self.depth = 0

    def assignPlayOrder(self):
        nextPlayOrder = [0]
        self.__assignPlayOrder(nextPlayOrder)

    def __assignPlayOrder(self, nextPlayOrder):
        self.playOrder = nextPlayOrder[0]
        nextPlayOrder[0] = self.playOrder + 1
        for child in self.children:
            child.__assignPlayOrder(nextPlayOrder)


class EpubItem:
    def __init__(self, id='', srcPath='', destPath='', mimeType='', html=''):
        self.id = id
        self.srcPath = srcPath
        self.destPath = destPath
        self.mimeType = mimeType
        self.html = html


class EpubBook:
    def __init__(self, template_dir="templates"):
        self.loader = TemplateLoader(template_dir)

        self.rootDir = ''
        self.UUID = uuid.uuid1()

        self.lang = 'en-US'
        self.title = ''
        self.creators = []
        self.metaInfo = []

        self.imageItems = {}
        self.htmlItems = {}
        self.cssItems = {}
        self.scriptItems = {}

        self.coverImage = None
        self.titlePage = None
        self.tocPage = None

        self.spine = []
        self.guide = {}
        self.tocMapRoot = TocMapNode()
        self.lastNodeAtDepth = {0: self.tocMapRoot}

    def setTitle(self, title):
        self.title = title

    def setLang(self, lang):
        self.lang = lang

    def addCreator(self, name, role='aut'):
        self.creators.append((name, role))

    def addMeta(self, metaName, metaValue, **metaAttrs):
        self.metaInfo.append((metaName, metaValue, metaAttrs))

    def getMetaTags(self):
        l = []
        for metaName, metaValue, metaAttr in self.metaInfo:
            beginTag = '<dc:%s' % metaName
            if metaAttr:
                for attrName, attrValue in metaAttr.iteritems():
                    beginTag += ' opf:%s="%s"' % (attrName, attrValue)
            beginTag += '>'
            endTag = '</dc:%s>' % metaName
            l.append((beginTag, metaValue, endTag))
        return l

    def getImageItems(self):
        return sorted(self.imageItems.values(), key=lambda x: x.id)

    def getHtmlItems(self):
        return sorted(self.htmlItems.values(), key=lambda x: x.id)

    def getCssItems(self):
        return sorted(self.cssItems.values(), key=lambda x: x.id)

    def getScriptItems(self):
        return sorted(self.scriptItems.values(), key=lambda x: x.id)

    def getAllItems(self):
        return sorted(
            itertools.chain(
                self.imageItems.values(),
                self.htmlItems.values(),
                self.cssItems.values(),
                self.scriptItems.values()), key=lambda x: x.id)

    def summary(self):
        s = [('HTML', len(self.htmlItems)),
             ('CSS', len(self.cssItems)),
             ('JS', len(self.scriptItems)),
             ('Images', len(self.imageItems))]
        return '\n'.join(["%s: %d" % (l, n) for (l, n) in s])

    def addImage(self, srcPath, destPath):
        item = EpubItem(
            id='image_%d' % (len(self.imageItems) + 1),
            srcPath=srcPath,
            destPath=destPath,
            mimeType=mimetypes.guess_type(destPath)[0],
            html=None,
        )
        if item.destPath not in self.imageItems:
            self.imageItems[item.destPath] = item
        return self.imageItems[item.destPath]

    def addHtmlForImage(self, imageItem):
        tmpl = self.loader.load('image.html')
        stream = tmpl.generate(book=self, item=imageItem)
        html = stream.render('xhtml',
                             doctype='xhtml11',
                             drop_xml_decl=False)
        return self.addHtml('', '%s.html' % imageItem.destPath, html)

    def addHtml(self, srcPath, destPath, html=None):
        item = EpubItem(
            id='html_%d' % (len(self.htmlItems) + 1),
            srcPath=srcPath,
            destPath=destPath,
            html=html,
            mimeType='application/xhtml+xml')
        if item.destPath not in self.htmlItems:
            self.htmlItems[item.destPath] = item
        return self.htmlItems[item.destPath]

    def addCss(self, srcPath, destPath):
        item = EpubItem(
            id='css_%d' % (len(self.cssItems) + 1),
            srcPath=srcPath,
            destPath=destPath,
            mimeType='text/css')
        if item.destPath not in self.cssItems:
            self.cssItems[item.destPath] = item
        return self.cssItems[item.destPath]

    def addScript(self, srcPath, destPath):
        item = EpubItem(
            id='js_%d' % (len(self.scriptItems) + 1),
            srcPath=srcPath,
            destPath=destPath,
            mimeType='text/javascript')
        if item.destPath not in self.scriptItems:
            self.scriptItems[item.destPath] = item
        return self.scriptItems[item.destPath]

    def addCover(self, srcPath):
        assert not self.coverImage
        _, ext = os.path.splitext(srcPath)
        destPath = 'cover%s' % ext
        self.coverImage = self.addImage(srcPath, destPath)

    def __makeTitlePage(self):
        assert self.titlePage
        if self.titlePage.html:
            return
        tmpl = self.loader.load('title-page.html')
        stream = tmpl.generate(book=self)
        self.titlePage.html = stream.render(
            'xhtml', doctype='xhtml11', drop_xml_decl=False)

    def addTitlePage(self, html=''):
        assert not self.titlePage
        self.titlePage = self.addHtml('', 'title-page.html', html)
        self.addSpineItem(self.titlePage, True, -200)
        self.addGuideItem('title-page.html', 'Title Page', 'title-page')

    def __makeTocPage(self):
        assert self.tocPage
        tmpl = self.loader.load('toc.html')
        stream = tmpl.generate(book=self)
        self.tocPage.html = stream.render(
            'xhtml', doctype='xhtml11', drop_xml_decl=False)

    def addTocPage(self):
        assert not self.tocPage
        self.tocPage = self.addHtml('', 'toc.html', '')
        self.addSpineItem(self.tocPage, False, -100)
        self.addGuideItem('toc.html', 'Table of Contents', 'toc')

    def getSpine(self):
        return sorted(self.spine)

    def addSpineItem(self, item, linear=True, order=None):
        assert item.destPath in self.htmlItems
        if order is None:
            order = (max(order for order, _, _ in self.spine)
                     if self.spine else 0) + 1
        self.spine.append((order, item, linear))

    def getGuide(self):
        return sorted(self.guide.values(), key=lambda x: x[2])

    def addGuideItem(self, href, title, type):
        assert type not in self.guide
        self.guide[type] = (href, title, type)

    def getTocMapRoot(self):
        return self.tocMapRoot

    def getTocMapHeight(self):
        return max(self.lastNodeAtDepth.keys())

    def addTocMapNode(self, href, title, depth=None, parent=None):
        node = TocMapNode()
        node.href = href
        node.title = title
        if parent is None:
            if depth is None:
                parent = self.tocMapRoot
            else:
                parent = self.lastNodeAtDepth[depth - 1]
        parent.children.append(node)
        node.depth = parent.depth + 1
        self.lastNodeAtDepth[node.depth] = node
        return node

    def makeDirs(self):
        try:
            os.makedirs(os.path.join(self.rootDir, 'META-INF'))
        except OSError:
            pass
        try:
            os.makedirs(os.path.join(self.rootDir, 'OEBPS'))
        except OSError:
            pass

    def __writeContainerXML(self):
        fout = open(
            os.path.join(self.rootDir, 'META-INF', 'container.xml'), 'w')
        tmpl = self.loader.load('container.xml')
        stream = tmpl.generate()
        fout.write(stream.render('xml'))
        fout.close()

    def __writeTocNCX(self):
        self.tocMapRoot.assignPlayOrder()
        fout = open(os.path.join(self.rootDir, 'OEBPS', 'toc.ncx'), 'w')
        tmpl = self.loader.load('toc.ncx')
        stream = tmpl.generate(book=self)
        fout.write(stream.render('xml'))
        fout.close()

    def __writeContentOPF(self):
        fout = open(os.path.join(self.rootDir, 'OEBPS', 'content.opf'), 'w')
        tmpl = self.loader.load('content.opf')
        stream = tmpl.generate(book=self)
        fout.write(stream.render('xml'))
        fout.close()

    def __writeItems(self):
        items = self.getAllItems()
        for item in items:
            outname = os.path.join(self.rootDir, 'OEBPS', item.destPath)
            if item.html:
                fout = open(outname, 'w')
                fout.write(item.html)
                fout.close()
            else:
                shutil.copyfile(item.srcPath, outname)

    def __writeMimeType(self):
        fout = open(os.path.join(self.rootDir, 'mimetype'), 'w')
        fout.write('application/epub+zip')
        fout.close()

    @staticmethod
    def __listManifestItems(contentOPFPath):
        tree = etree.parse(contentOPFPath)
        return tree.xpath("//opf:manifest/opf:item/@href",
                          namespaces={'opf': 'http://www.idpf.org/2007/opf'})

    @staticmethod
    def createArchive(rootDir, outputPath):
        fout = zipfile.ZipFile(outputPath, 'w')
        cwd = os.getcwd()
        os.chdir(rootDir)
        fout.write('mimetype', compress_type=zipfile.ZIP_STORED)
        fileList = []
        fileList.append(os.path.join('META-INF', 'container.xml'))
        fileList.append(os.path.join('OEBPS', 'content.opf'))
        for itemPath in EpubBook.__listManifestItems(
                os.path.join('OEBPS', 'content.opf')):
            fileList.append(os.path.join('OEBPS', itemPath))
        for filePath in fileList:
            fout.write(filePath, compress_type=zipfile.ZIP_DEFLATED)
        fout.close()
        os.chdir(cwd)

    @staticmethod
    def checkEpub(checkerPath, epubPath):
        subprocess.call(['java', '-jar', checkerPath, epubPath], shell=True)

    def createBook(self, rootDir):
        if self.titlePage:
            self.__makeTitlePage()
        if self.tocPage:
            self.__makeTocPage()
        self.rootDir = rootDir
        self.makeDirs()
        self.__writeMimeType()
        self.__writeItems()
        self.__writeContainerXML()
        self.__writeContentOPF()
        self.__writeTocNCX()
