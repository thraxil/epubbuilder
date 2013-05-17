from epubbuilder import epub
from unittest import TestCase
import os.path
import zipfile


def getMinimalHtml(text):
    return ("""<!DOCTYPE html PUBLIC "-//W3C//DTD XHtml 1.1//EN" """
            """"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>%s</title></head>
<body><p>%s</p></body>
</html>
""") % (text, text)


class TestAPI(TestCase):
    def setUp(self):
        self.book = epub.EpubBook()
        self.book.setTitle('Most Wanted Tips for Aspiring Young Pirates')
        self.book.addCreator('Monkey D Luffy')
        self.book.addCreator('Guybrush Threepwood')
        self.book.addMeta('contributor', 'Smalltalk80', role='bkp')
        self.book.addMeta('date', '2010', event='publication')

        self.book.addTitlePage()
        self.book.addTocPage()
        self.book.addCover(r'test_data/ccnmtl.gif')

        self.book.addCss(r'test_data/main.css', 'main.css')

        n1 = self.book.addHtml('', '1.html', getMinimalHtml('Chapter 1'))
        n11 = self.book.addHtml('', '2.html', getMinimalHtml('Section 1.1'))
        n111 = self.book.addHtml('', '3.html',
                                 getMinimalHtml('Subsection 1.1.1'))
        n12 = self.book.addHtml('', '4.html', getMinimalHtml('Section 1.2'))
        n2 = self.book.addHtml('', '5.html', getMinimalHtml('Chapter 2'))

        self.book.addSpineItem(n1)
        self.book.addSpineItem(n11)
        self.book.addSpineItem(n111)
        self.book.addSpineItem(n12)
        self.book.addSpineItem(n2)

        self.book.addTocMapNode(n1.destPath, '1')
        self.book.addTocMapNode(n11.destPath, '1.1', 2)
        self.book.addTocMapNode(n111.destPath, '1.1.1', 3)
        self.book.addTocMapNode(n12.destPath, '1.2', 2)
        self.book.addTocMapNode(n2.destPath, '2')

        # make a second book using some of the fileobj stuff instead
        self.im_book = epub.EpubBook()
        self.im_book.setTitle('Most Wanted Tips for Aspiring Young Pirates')
        self.im_book.addCreator('Monkey D Luffy')
        self.im_book.addCreator('Guybrush Threepwood')
        self.im_book.addMeta('contributor', 'Smalltalk80', role='bkp')
        self.im_book.addMeta('date', '2010', event='publication')

        self.im_book.addTitlePage()
        self.im_book.addTocPage()

        self.im_book.addCover(
            fileobj=open(r'test_data/ccnmtl.gif'),
            ext='.gif')

        self.im_book.addCss(
            destPath='main.css',
            fileobj=open(r'test_data/main.css', 'rb'))

        n1 = self.im_book.addHtml('', '1.html', getMinimalHtml('Chapter 1'))
        n11 = self.im_book.addHtml('', '2.html', getMinimalHtml('Section 1.1'))
        n111 = self.im_book.addHtml('', '3.html',
                                    getMinimalHtml('Subsection 1.1.1'))
        n12 = self.im_book.addHtml('', '4.html', getMinimalHtml('Section 1.2'))
        n2 = self.im_book.addHtml('', '5.html', getMinimalHtml('Chapter 2'))

        self.im_book.addSpineItem(n1)
        self.im_book.addSpineItem(n11)
        self.im_book.addSpineItem(n111)
        self.im_book.addSpineItem(n12)
        self.im_book.addSpineItem(n2)

        self.im_book.addTocMapNode(n1.destPath, '1')
        self.im_book.addTocMapNode(n11.destPath, '1.1', 2)
        self.im_book.addTocMapNode(n111.destPath, '1.1.1', 3)
        self.im_book.addTocMapNode(n12.destPath, '1.2', 2)
        self.im_book.addTocMapNode(n2.destPath, '2')

    def tearDown(self):
        pass

    def test_endtoend(self):
        expected = """HTML: 7\nCSS: 1\nJS: 0\nImages: 1"""
        self.assertEqual(self.book.summary(), expected)

        expected = (
            """<?xml version="1.0" encoding="UTF-8" """
            """standalone="no"?>\n<container xmlns="urn:"""
            """oasis:names:tc:opendocument:xmlns:container" """
            """version="1.0">\n  <rootfiles>\n    <rootfile """
            """full-path="OEBPS/content.opf" media-type="application/"""
            """oebps-package+xml"/>\n  </rootfiles>\n</container>""")
        self.assertEqual(self.book.container_xml(), expected)

        self.assertIn("<navMap", self.book.toc_ncx())

        self.assertIn("<opf:item", self.book.content_opf())

        rootDir = r'test_output/test0'
        self.book.createBook(rootDir)
        epub.EpubBook.createArchive(rootDir, rootDir + '.epub')
        self.assertTrue(os.path.exists(rootDir))
        self.assertTrue(os.path.exists(rootDir + '.epub'))

    def test_disk_to_memory(self):
        # our book read in from a directory should
        # be able to write out to a zipfile
        out = self.book.make_epub()
        # try parsing it as a zipfile
        zipfile.ZipFile(out, "r")

    def test_memory_to_memory(self):
        """ the book that's constructed entirely in memory also should work """
        out = self.im_book.make_epub()
        z = zipfile.ZipFile(out, "r")
        print z.namelist()

        assert 'mimetype' in z.namelist()
        assert 'OEBPS/cover.gif' in z.namelist()
        assert 'OEBPS/main.css' in z.namelist()

        assert '/* main.css test file */' in z.read('OEBPS/main.css')
