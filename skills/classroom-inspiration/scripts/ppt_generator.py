#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
课堂灵感生成器 · PPT 生成模块
=================================
使用 python-pptx 生成教学课件。
基于 SKILL.md 第 3.13~3.14 节的规范实现。

用法:
    from ppt_generator import PPTBuilder
    builder = PPTBuilder()
    builder.add_cover("闯关三连 · 直线与圆", "高二数学 · 选择性必修第一册")
    builder.add_slide(...)
    builder.save("C:\\Users\\...\\课件.pptx")
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

# ─────────────────────────────────────────────
# 配色方案（学科预设）
# ─────────────────────────────────────────────
SCHEMES = {
    "math": {  # 数学
        "primary": RGBColor(0x1A, 0x3C, 0x6E),
        "secondary": RGBColor(0x5B, 0x9B, 0xD5),
        "accent": RGBColor(0xF0, 0x8C, 0x00),
        "bg": RGBColor(0xFF, 0xFF, 0xFF),
        "light_bg": RGBColor(0xF0, 0xF2, 0xF5),
        "text": RGBColor(0x2C, 0x2C, 0x2C),
        "muted": RGBColor(0x99, 0x99, 0x99),
        "white": RGBColor(0xFF, 0xFF, 0xFF),
        "success": RGBColor(0x2E, 0x9E, 0x8F),
        "warning": RGBColor(0xE8, 0x85, 0x2E),
        "purple": RGBColor(0x7B, 0x4E, 0xA3),
    },
    "chinese": {  # 语文
        "primary": RGBColor(0x8B, 0x45, 0x13),
        "secondary": RGBColor(0xD2, 0x69, 0x1E),
        "accent": RGBColor(0xFF, 0xD7, 0x00),
        "bg": RGBColor(0xFF, 0xFF, 0xFF),
        "light_bg": RGBColor(0xF9, 0xF5, 0xF0),
        "text": RGBColor(0x2C, 0x2C, 0x2C),
        "muted": RGBColor(0x99, 0x99, 0x99),
        "white": RGBColor(0xFF, 0xFF, 0xFF),
    },
    "default": {
        "primary": RGBColor(0x2B, 0x57, 0x9A),
        "secondary": RGBColor(0x5B, 0x9B, 0xD5),
        "accent": RGBColor(0xE8, 0x6C, 0x00),
        "bg": RGBColor(0xFF, 0xFF, 0xFF),
        "light_bg": RGBColor(0xF5, 0xF5, 0xF5),
        "text": RGBColor(0x2C, 0x2C, 0x2C),
        "muted": RGBColor(0x99, 0x99, 0x99),
        "white": RGBColor(0xFF, 0xFF, 0xFF),
    },
}

def _set_font(run, name="微软雅黑", size=None, bold=False, color=None):
    """设置字体（含东亚字体回退）"""
    run.font.name = name
    if size:
        run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    rPr.set(qn('a:ea'), name)
    rPr.set(qn('a:latin'), name)

def _add_textbox(slide, left, top, width, height):
    return slide.shapes.add_textbox(left, top, width, height)

def _set_para(p, text, size=14, color=None, bold=False, align=PP_ALIGN.LEFT, spacing=None):
    p.text = text
    _set_font(p.runs[0] if p.runs else p.add_run(), size=size, bold=bold, color=color)
    p.alignment = align
    if spacing:
        p.line_spacing = Pt(spacing)
    return p

def _add_shape(slide, left, top, width, height, fill_color=None, line_color=None, line_width=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.line.fill.background()
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    if line_color:
        shape.line.color.rgb = line_color
        if line_width:
            shape.line.width = Pt(line_width)
    return shape

def _add_para(tf, text, size=14, color=None, bold=False, align=PP_ALIGN.LEFT, space_before=Pt(2)):
    p = tf.add_paragraph()
    p.text = text
    _set_font(p.runs[0] if p.runs else p.add_run(), size=size, bold=bold, color=color)
    p.alignment = align
    p.space_before = space_before
    return p

class PPTBuilder:
    """PPT 课件构建器"""

    SLIDE_W = Inches(13.333)
    SLIDE_H = Inches(7.5)

    def __init__(self, scheme="default"):
        self.prs = Presentation()
        self.prs.slide_width = self.SLIDE_W
        self.prs.slide_height = self.SLIDE_H
        self.c = SCHEMES.get(scheme, SCHEMES["default"])
        self._page_num = 0

    # ── 基础幻灯片类型 ──────────────────────

    def add_blank_slide(self):
        self._page_num += 1
        return self.prs.slides.add_slide(self.prs.slide_layouts[6])

    # ── 1. 封面 ──────────────────────────────

    def add_cover(self, title, subtitle="", teacher="", extra_info="",
                  bg_color=None, accent_color=None):
        """全幅深色背景 + 标题 + 装饰色条"""
        slide = self.add_blank_slide()
        bg = bg_color or self.c["primary"]
        _add_shape(slide, Inches(0), Inches(0), self.SLIDE_W, self.SLIDE_H, fill_color=bg)

        # 装饰性色块
        ac = accent_color or self.c["accent"]
        _add_shape(slide, Inches(0), Inches(0), Inches(0.3), self.SLIDE_H, fill_color=ac)

        # 主标题
        txb = _add_textbox(slide, Inches(1.5), Inches(1.8), Inches(10), Inches(1.5))
        _set_para(txb.text_frame.paragraphs[0], title, size=44, color=self.c["white"], bold=True)

        # 副标题
        if subtitle:
            txb = _add_textbox(slide, Inches(1.5), Inches(3.3), Inches(10), Inches(0.8))
            _set_para(txb.text_frame.paragraphs[0], subtitle, size=22, color=RGBColor(0xBB, 0xCC, 0xDD))

        # 分隔线
        _add_shape(slide, Inches(1.5), Inches(4.3), Inches(3), Inches(0.05), fill_color=ac)

        # 教师/课时信息
        if teacher:
            txb = _add_textbox(slide, Inches(1.5), Inches(4.8), Inches(8), Inches(0.5))
            _set_para(txb.text_frame.paragraphs[0], teacher, size=18, color=RGBColor(0xCC, 0xDD, 0xEE))

        if extra_info:
            txb = _add_textbox(slide, Inches(1.5), Inches(5.4), Inches(8), Inches(0.5))
            _set_para(txb.text_frame.paragraphs[0], extra_info, size=16, color=RGBColor(0xAA, 0xBB, 0xCC))

        # 底部装饰条
        _add_shape(slide, Inches(0), Inches(7.0), self.SLIDE_W, Inches(0.5), fill_color=ac)

        return slide

    # ── 2. 内容页（标题栏 + 白色内容区） ────

    def add_content_slide(self, title, subtitle="", body_func=None):
        """标准内容页：深蓝标题栏 + 白色正文区"""
        slide = self.add_blank_slide()
        # 标题栏
        _add_shape(slide, Inches(0), Inches(0), self.SLIDE_W, Inches(1.1), fill_color=self.c["primary"])
        txb = _add_textbox(slide, Inches(0.6), Inches(0.15), Inches(12), Inches(0.7))
        _set_para(txb.text_frame.paragraphs[0], title, size=28, color=self.c["white"], bold=True)
        if subtitle:
            txb = _add_textbox(slide, Inches(0.6), Inches(0.7), Inches(12), Inches(0.4))
            _set_para(txb.text_frame.paragraphs[0], subtitle, size=14, color=RGBColor(0xBB, 0xCC, 0xDD))
        # 底部装饰线
        _add_shape(slide, Inches(0), Inches(7.3), self.SLIDE_W, Inches(0.2), fill_color=self.c["primary"])
        if body_func:
            body_func(slide)
        return slide

    # ── 3. 过渡页 ────────────────────────────

    def add_transition_slide(self, section_num, section_title, subtitle="",
                             accent_color=None):
        """章节过渡页：纯色块 + 大号编号 + 标题"""
        slide = self.add_blank_slide()
        ac = accent_color or self.c["accent"]
        _add_shape(slide, Inches(0), Inches(0), Inches(5.5), self.SLIDE_H, fill_color=ac)

        # 大号编号
        txb = _add_textbox(slide, Inches(0.5), Inches(2.0), Inches(4.5), Inches(1.5))
        _set_para(txb.text_frame.paragraphs[0], str(section_num),
                  size=72, color=self.c["white"], bold=True, align=PP_ALIGN.CENTER)

        # 标题
        txb = _add_textbox(slide, Inches(0.5), Inches(3.5), Inches(4.5), Inches(1.0))
        _set_para(txb.text_frame.paragraphs[0], section_title,
                  size=36, color=self.c["white"], bold=True, align=PP_ALIGN.CENTER)

        if subtitle:
            txb = _add_textbox(slide, Inches(0.5), Inches(4.5), Inches(4.5), Inches(1.5))
            _set_para(txb.text_frame.paragraphs[0], subtitle,
                      size=16, color=self.c["white"], align=PP_ALIGN.CENTER)

        # 右侧说明区
        return slide

    # ── 4. 纯文本内容 ────────────────────────

    def add_text_slide(self, title, items, font_size=15, col_count=1, accent=None):
        """多行文本页（支持分栏）"""
        ac = accent or self.c["primary"]
        def body(slide):
            left = Inches(0.8)
            top = Inches(1.5)
            w = Inches(11.5) if col_count == 1 else Inches(5.5)
            gap = Inches(0.5)
            line_h = Inches(0.45)

            for col in range(col_count):
                x = left + col * (w + gap)
                for i, item in enumerate(items if col_count == 1 else items[col]):
                    y = top + i * line_h
                    txb = _add_textbox(slide, x, y, w, line_h)
                    p = txb.text_frame.paragraphs[0]
                    prefix = ""
                    text = item
                    if isinstance(item, tuple):
                        prefix, text = item
                    final = f"{prefix} {text}" if prefix else text
                    _set_para(p, final, size=font_size, color=self.c["text"])

        return self.add_content_slide(title, body_func=body)

    # ── 5. 提醒/强调框 ───────────────────────

    def add_callout_box(self, slide, text, top, left=None, width=None, height=None,
                        bg_color=None, border_color=None, font_size=13):
        l = left or Inches(0.5)
        w = width or Inches(12.3)
        h = height or Inches(0.6)
        bg = bg_color or RGBColor(0xFF, 0xF3, 0xE0)
        bc = border_color or self.c["accent"]
        _add_shape(slide, l, top, w, h, fill_color=bg, line_color=bc, line_width=1)
        txb = _add_textbox(slide, l + Inches(0.3), top + Inches(0.05), w - Inches(0.6), h - Inches(0.1))
        _set_para(txb.text_frame.paragraphs[0], text, size=font_size, color=self.c["text"])
        return slide

    # ── 6. 对比双栏页 ────────────────────────

    def add_comparison_slide(self, title, left_heading, right_heading,
                             left_items, right_items, accent_color=None):
        """左右对比双栏页"""
        ac = accent_color or self.c["primary"]
        def body(slide):
            # 左栏
            _add_shape(slide, Inches(0.5), Inches(1.4), Inches(5.8), Inches(5.5),
                       fill_color=self.c["light_bg"])
            _add_shape(slide, Inches(0.5), Inches(1.4), Inches(5.8), Inches(0.7),
                       fill_color=accent_color or self.c["accent"])
            txb = _add_textbox(slide, Inches(0.5), Inches(1.4), Inches(5.8), Inches(0.7))
            _set_para(txb.text_frame.paragraphs[0], left_heading,
                      size=20, color=self.c["white"], bold=True, align=PP_ALIGN.CENTER)
            for i, item in enumerate(left_items):
                txb = _add_textbox(slide, Inches(0.8), Inches(2.3 + i * 0.7), Inches(5.2), Inches(0.6))
                _set_para(txb.text_frame.paragraphs[0], item, size=14, color=self.c["text"])

            # 右栏
            _add_shape(slide, Inches(6.8), Inches(1.4), Inches(5.8), Inches(5.5),
                       fill_color=self.c["light_bg"])
            _add_shape(slide, Inches(6.8), Inches(1.4), Inches(5.8), Inches(0.7),
                       fill_color=ac)
            txb = _add_textbox(slide, Inches(6.8), Inches(1.4), Inches(5.8), Inches(0.7))
            _set_para(txb.text_frame.paragraphs[0], right_heading,
                      size=20, color=self.c["white"], bold=True, align=PP_ALIGN.CENTER)
            for i, item in enumerate(right_items):
                txb = _add_textbox(slide, Inches(7.1), Inches(2.3 + i * 0.7), Inches(5.2), Inches(0.6))
                _set_para(txb.text_frame.paragraphs[0], item, size=14, color=self.c["text"])

        return self.add_content_slide(title, body_func=body)

    # ── 7. 表格页 ────────────────────────────

    def add_table_slide(self, title, headers, rows, col_widths=None, accent_color=None):
        """表格数据页"""
        ac = accent_color or self.c["primary"]
        def body(slide):
            n_rows = len(rows) + 1
            n_cols = len(headers)
            left = Inches(0.8)
            top = Inches(1.4)
            width = Inches(11.5)
            row_h = Inches(0.45)
            height = row_h * n_rows
            tbl_shape = slide.shapes.add_table(n_rows, n_cols, left, top, width, height)
            tbl = tbl_shape.table

            # 表头
            for j, h in enumerate(headers):
                cell = tbl.cell(0, j)
                cell.text = h
                for p in cell.text_frame.paragraphs:
                    _set_font(p.runs[0] if p.runs else p.add_run(), size=13, bold=True, color=self.c["white"])
                    p.alignment = PP_ALIGN.CENTER
                cell.fill.solid()
                cell.fill.fore_color.rgb = ac

            # 数据行
            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    cell = tbl.cell(i + 1, j)
                    cell.text = str(val)
                    for p in cell.text_frame.paragraphs:
                        _set_font(p.runs[0] if p.runs else p.add_run(), size=12, color=self.c["text"])
                    if i % 2 == 1:
                        cell.fill.solid()
                        cell.fill.fore_color.rgb = RGBColor(0xF5, 0xF5, 0xF5)

        return self.add_content_slide(title, body_func=body)

    # ── 8. 全图背景视觉页 ────────────────────

    def add_visual_slide(self, title, body_text=None, overlay_alpha=0.45,
                         title_color=None, title_pos="center"):
        """全图背景 + 半透明遮罩 + 前景文字（适合封面/过渡/结尾）
        注意：本函数生成纯色背景版本，如需实际图片需传入 img_path/img_url"""
        slide = self.add_blank_slide()

        # 纯色背景（替代图片）
        _add_shape(slide, Inches(0), Inches(0), self.SLIDE_W, self.SLIDE_H,
                   fill_color=self.c["primary"])

        # 装饰几何元素（用略浅的同色系）
        def _lighten(c, amt):
            r = min(255, c[0] + amt)
            g = min(255, c[1] + amt)
            b = min(255, c[2] + amt)
            return RGBColor(r, g, b)
        prim_tuple = self.c["primary"]  # tuple-like: [0]=R, [1]=G, [2]=B
        _add_shape(slide, Inches(10), Inches(5), Inches(3.5), Inches(3.5),
                   fill_color=_lighten(prim_tuple, 20))
        _add_shape(slide, Inches(8.5), Inches(-1), Inches(3), Inches(3),
                   fill_color=_lighten(prim_tuple, 15))

        tc = title_color or self.c["white"]
        if title_pos == "center":
            txb = _add_textbox(slide, Inches(1.5), Inches(2.5), Inches(10), Inches(2))
            _set_para(txb.text_frame.paragraphs[0], title, size=44, color=tc, bold=True, align=PP_ALIGN.CENTER)
            if body_text:
                txb2 = _add_textbox(slide, Inches(2), Inches(4.5), Inches(9), Inches(2))
                _set_para(txb2.text_frame.paragraphs[0], body_text, size=22, color=RGBColor(0xDD, 0xDD, 0xDD),
                          align=PP_ALIGN.CENTER)
        else:
            txb = _add_textbox(slide, Inches(1.5), Inches(2.0), Inches(6), Inches(1.5))
            _set_para(txb.text_frame.paragraphs[0], title, size=44, color=tc, bold=True, align=PP_ALIGN.LEFT)
            if body_text:
                txb2 = _add_textbox(slide, Inches(1.5), Inches(4.0), Inches(8), Inches(2))
                _set_para(txb2.text_frame.paragraphs[0], body_text, size=22, color=RGBColor(0xDD, 0xDD, 0xDD),
                          align=PP_ALIGN.LEFT)

        return slide

    # ── 9. 卡片网格型 ────────────────────────

    def add_card_grid(self, title, cards, accent_color=None):
        """卡片网格：2-4张卡片并排，每张含小图+标题+描述"""
        ac = accent_color or self.c["primary"]
        def body(slide):
            n = len(cards)
            card_w = Inches(3.5)
            card_h = Inches(3.8)
            gap = Inches(0.4)
            total_w = n * card_w + (n - 1) * gap
            start_x = Inches(0.8)

            for i, card in enumerate(cards):
                x = start_x + i * (card_w + gap)
                y = Inches(1.4)
                bg = _add_shape(slide, x, y, card_w, card_h, fill_color=self.c["light_bg"])
                bg.line.color.rgb = ac
                bg.line.width = Pt(1.5)

                # 编号标记
                num_shape = _add_shape(slide, x + Inches(0.15), y + Inches(0.2),
                                       Inches(0.6), Inches(0.6), fill_color=ac)
                txb = _add_textbox(slide, x + Inches(0.15), y + Inches(0.2),
                                   Inches(0.6), Inches(0.6))
                _set_para(txb.text_frame.paragraphs[0], str(i + 1),
                          size=18, color=self.c["white"], bold=True, align=PP_ALIGN.CENTER)

                # 标题
                txb = _add_textbox(slide, x + Inches(0.9), y + Inches(0.25),
                                   card_w - Inches(1.2), Inches(0.5))
                _set_para(txb.text_frame.paragraphs[0], card.get("title", ""),
                          size=18, color=ac, bold=True)

                # 描述行
                for j, line in enumerate(card.get("items", [])):
                    txb = _add_textbox(slide, x + Inches(0.2), y + Inches(1.1 + j * 0.5),
                                       card_w - Inches(0.4), Inches(0.5))
                    _set_para(txb.text_frame.paragraphs[0], line,
                              size=13, color=self.c["text"])

        return self.add_content_slide(title, body_func=body)

    # ── 10. 活动步骤页 ───────────────────────

    def add_activity_slide(self, title, steps, accent_color=None, duration=""):
        """步骤式活动页：编号步骤 + 说明"""
        ac = accent_color or self.c["accent"]
        def body(slide):
            for i, (step, desc) in enumerate(steps):
                y = Inches(1.5) + i * Inches(1.5)
                badge = _add_shape(slide, Inches(0.5), y, Inches(1.0), Inches(0.5),
                                   fill_color=ac)
                txb = _add_textbox(slide, Inches(0.5), y, Inches(1.0), Inches(0.5))
                _set_para(txb.text_frame.paragraphs[0], step,
                          size=12, color=self.c["white"], bold=True, align=PP_ALIGN.CENTER)
                txb = _add_textbox(slide, Inches(1.8), y + Inches(0.0), Inches(10.5), Inches(1.0))
                _set_para(txb.text_frame.paragraphs[0], desc, size=14, color=self.c["text"])

            if duration:
                txb = _add_textbox(slide, Inches(0.5), Inches(6.5), Inches(4), Inches(0.4))
                _set_para(txb.text_frame.paragraphs[0], f"⏱ {duration}",
                          size=14, color=self.c["muted"], bold=True)

        return self.add_content_slide(title, body_func=body)

    # ── 11. 引用/名言页 ──────────────────────

    def add_quote_slide(self, quote, author="", accent_color=None):
        """大字号引用居中页"""
        slide = self.add_blank_slide()
        ac = accent_color or self.c["accent"]
        txb = _add_textbox(slide, Inches(1.5), Inches(2.0), Inches(10), Inches(3.0))
        tf = txb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        _set_para(p, f"「{quote}」", size=36, color=ac, bold=False, align=PP_ALIGN.CENTER)
        if author:
            txb2 = _add_textbox(slide, Inches(1.5), Inches(5.2), Inches(10), Inches(1.0))
            _set_para(txb2.text_frame.paragraphs[0], f"—— {author}",
                      size=20, color=self.c["muted"], align=PP_ALIGN.RIGHT)
        return slide

    # ── 12. 结尾页 ───────────────────────────

    def add_closing_slide(self, main_text, sub_text="", accent_color=None):
        """结尾总结页"""
        slide = self.add_blank_slide()
        _add_shape(slide, Inches(0), Inches(0), self.SLIDE_W, self.SLIDE_H,
                   fill_color=self.c["primary"])
        ac = accent_color or self.c["accent"]
        _add_shape(slide, Inches(0), Inches(6.8), self.SLIDE_W, Inches(0.7),
                   fill_color=ac)

        txb = _add_textbox(slide, Inches(1.5), Inches(2.0), Inches(10), Inches(2.0))
        _set_para(txb.text_frame.paragraphs[0], main_text,
                  size=36, color=self.c["white"], bold=True, align=PP_ALIGN.CENTER)

        if sub_text:
            txb2 = _add_textbox(slide, Inches(1.5), Inches(4.0), Inches(10), Inches(1.5))
            _set_para(txb2.text_frame.paragraphs[0], sub_text,
                      size=20, color=RGBColor(0xCC, 0xDD, 0xEE), align=PP_ALIGN.CENTER)

        return slide

    # ── 辅助：添加课本追溯标签 ──────────────

    def add_textbook_label(self, slide, label_text, color=None):
        """右下角课本页码追溯标签"""
        txb = _add_textbox(slide, Inches(11.3), Inches(7.0), Inches(1.8), Inches(0.4))
        _set_para(txb.text_frame.paragraphs[0], label_text,
                  size=10, color=color or self.c["muted"], align=PP_ALIGN.RIGHT)

    # ── 辅助：添加演讲备注 ───────────────────

    def add_notes(self, slide, text):
        """为当前幻灯片添加演讲者备注"""
        try:
            notes_slide = slide.notes_slide
            notes_slide.notes_text_frame.text = text
        except:
            pass

    # ── 辅助：设置页面背景色 ────────────────

    def set_slide_bg(self, slide, color):
        bg = slide.background
        fill = bg.fill
        fill.solid()
        fill.fore_color.rgb = color

    # ── 保存 ─────────────────────────────────

    def save(self, output_path):
        """保存为 .pptx 文件"""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        self.prs.save(output_path)
        return output_path
