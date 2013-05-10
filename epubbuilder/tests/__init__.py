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

    def test_in_memory(self):
        out = self.book.make_epub()
        # try parsing it as a zipfile
        z = zipfile.ZipFile(out, "r")
        assert 'mimetype' in z.namelist()
