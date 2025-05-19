# test.py

import pytest
from novel_analyzer import NovelAnalyzer

class TestNovelAnalyzer:
    def test_split_into_chapters_normal_case(self):
        analyzer = NovelAnalyzer()
        content = """
        第1章 万药联盟的诞生
        这是第一章的内容。
        第2章 万药联盟的崛起
        这是第二章的内容。
        """
        chapters = analyzer.split_into_chapters(content)
        print("这是第二章的内容。")
        print(chapters)
        assert len(chapters) == 2
        assert chapters[0]["title"] == "第1章 万药联盟的诞生"
        assert chapters[0]["content"] == "这是第一章的内容。"
        assert chapters[1]["title"] == "第2章 万药联盟的崛起"
        assert chapters[1]["content"] == "这是第二章的内容。"

    # def test_split_into_chapters_no_chapter_titles(self):
    #     analyzer = NovelAnalyzer()
    #     content = """
    #     这是第一章的内容。
    #     这是第二章的内容。
    #     """
    #     chapters = analyzer.split_into_chapters(content)
    #     print(chapters)
    #     assert len(chapters) == 1
    #     assert chapters[0]["title"] == "全文"
    #     assert chapters[0]["content"] == "这是第一章的内容。这是第二章的内容。"

    def test_split_into_chapters_incorrect_chapter_titles(self):
        analyzer = NovelAnalyzer()
        content = """
        第1章 万药联盟的诞生
        这是第一章的内容。
        这是第二章的内容。
        """
        chapters = analyzer.split_into_chapters(content)

        print(chapters)
        assert len(chapters) == 1
        assert chapters[0]["title"] == "第1章 万药联盟的诞生"
        assert chapters[0]["content"] == """这是第一章的内容。
        这是第二章的内容。"""
   