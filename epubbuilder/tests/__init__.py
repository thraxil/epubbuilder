from epubbuilder import epub
from unittest import TestCase
import os.path


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
        pass

    def tearDown(self):
        pass

    def test_endtoend(self):
        book = epub.EpubBook()
        book.setTitle("test title")
        book.setTitle('Most Wanted Tips for Aspiring Young Pirates')
        book.addCreator('Monkey D Luffy')
        book.addCreator('Guybrush Threepwood')
        book.addMeta('contributor', 'Smalltalk80', role='bkp')
        book.addMeta('date', '2010', event='publication')

        book.addTitlePage()
        book.addTocPage()
        book.addCover(r'test_data/ccnmtl.gif')

        book.addCss(r'test_data/main.css', 'main.css')

        n1 = book.addHtml('', '1.html', getMinimalHtml('Chapter 1'))
        n11 = book.addHtml('', '2.html', getMinimalHtml('Section 1.1'))
        n111 = book.addHtml('', '3.html', getMinimalHtml('Subsection 1.1.1'))
        n12 = book.addHtml('', '4.html', getMinimalHtml('Section 1.2'))
        n2 = book.addHtml('', '5.html', getMinimalHtml('Chapter 2'))

        book.addSpineItem(n1)
        book.addSpineItem(n11)
        book.addSpineItem(n111)
        book.addSpineItem(n12)
        book.addSpineItem(n2)

        book.addTocMapNode(n1.destPath, '1')
        book.addTocMapNode(n11.destPath, '1.1', 2)
        book.addTocMapNode(n111.destPath, '1.1.1', 3)
        book.addTocMapNode(n12.destPath, '1.2', 2)
        book.addTocMapNode(n2.destPath, '2')

        expected = """HTML: 7\nCSS: 1\nJS: 0\nImages: 1"""
        self.assertEquals(book.summary(), expected)

        rootDir = r'test_output/test0'
        book.createBook(rootDir)
        epub.EpubBook.createArchive(rootDir, rootDir + '.epub')
        self.assertTrue(os.path.exists(rootDir))
        self.assertTrue(os.path.exists(rootDir + '.epub'))
