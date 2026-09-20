#!/usr/bin/env python3
"""Render shared knowledge-checklist JSON as a static A4 exam-revision handout.

All text is treated as plain text. All fonts are provided by --fonts, so builds
work without system fonts or a network connection. Optional reviewTopics are a web-only supplement. No self-assessment table,
selection, interactive form field, or review topic is rendered in the PDF.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, CondPageBreak, Frame, LongTable, PageBreak, PageTemplate, Paragraph,
    Spacer, Table, TableStyle, Flowable,
)

NAVY = colors.HexColor('#17334A')
INK = colors.HexColor('#253B49')
MUTED = colors.HexColor('#62737C')
RULE = colors.HexColor('#CFD8DC')
PALE = colors.HexColor('#F3F6F7')
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 15 * mm
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN
FRAME_HEIGHT = PAGE_HEIGHT - 2 * MARGIN - 19 * mm
MAX_WHOLE_ROW_HEIGHT = FRAME_HEIGHT - 150
FONT_FILES = {
    'ChecklistSerif': 'SourceSerif4-Regular.ttf',
    'ChecklistSerifSemibold': 'SourceSerif4-Semibold.ttf',
    'ChecklistSans': 'SourceSans3-Regular.ttf',
    'ChecklistSansSemibold': 'SourceSans3-Semibold.ttf',
    'ChecklistCJK': 'NotoSansSC-Regular.ttf',
}
DASH_TRANSLATION = str.maketrans({'\u2010': '-', '\u2011': '-', '\u2012': '-', '\u2013': '-', '\u2014': '-', '\u2212': '-'})


def normalized(text: str) -> str:
    return text.translate(DASH_TRANSLATION)


def register_fonts(directory: Path) -> None:
    for name, filename in FONT_FILES.items():
        path = directory / filename
        if not path.is_file():
            raise ValueError(f'Missing required bundled font: {path}')
        pdfmetrics.registerFont(TTFont(name, str(path)))
    pdfmetrics.registerFontFamily('ChecklistSans', normal='ChecklistSans', bold='ChecklistSansSemibold', italic='ChecklistSans', boldItalic='ChecklistSansSemibold')
    pdfmetrics.registerFontFamily('ChecklistSerif', normal='ChecklistSerif', bold='ChecklistSerifSemibold', italic='ChecklistSerif', boldItalic='ChecklistSerifSemibold')
    pdfmetrics.registerFontFamily('ChecklistCJK', normal='ChecklistCJK', bold='ChecklistCJK', italic='ChecklistCJK', boldItalic='ChecklistCJK')


def markup(text: str, font: str = 'ChecklistSans') -> str:
    """Escape text and choose an embedded font for every Unicode character."""
    text = normalized(text)
    primary = pdfmetrics.getFont(font).face.charToGlyph
    chinese = pdfmetrics.getFont('ChecklistCJK').face.charToGlyph
    runs: list[str] = []
    current_font: str | None = None
    current: list[str] = []
    for char in text:
        if char == '\n':
            if current:
                runs.append(f'<font name="{current_font}">{escape("".join(current))}</font>')
                current = []
            runs.append('<br/>')
            current_font = None
            continue
        if char == '\t':
            char = ' '
        cp = ord(char)
        if cp in primary:
            chosen = font
        elif cp in chinese:
            chosen = 'ChecklistCJK'
        else:
            raise ValueError(f'Unsupported character U+{cp:04X} {char!r}; add a licensed font that covers it.')
        if chosen != current_font:
            if current:
                runs.append(f'<font name="{current_font}">{escape("".join(current))}</font>')
                current = []
            current_font = chosen
        current.append(char)
    if current:
        runs.append(f'<font name="{current_font}">{escape("".join(current))}</font>')
    return ''.join(runs)


def text_value(value: object, path: str, optional: bool = False) -> str:
    if optional and value is None:
        return ''
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{path} must be a non-empty plain-text string')
    return value


def string_list(value: object, path: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError(f'{path} must be a non-empty list of plain-text strings')
    for item in value:
        text_value(item, path)
    return value


def integer(value: object, path: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError(f'{path} must be an integer from {minimum} to {maximum}')
    return value


def validate(data: object) -> dict:
    if not isinstance(data, dict):
        raise ValueError('The input must be a knowledge checklist object')
    for key in ('id', 'title', 'label', 'version', 'syllabus'):
        text_value(data.get(key), key)
    text_value(data.get('subtitle'), 'subtitle', optional=True)
    if 'sample' in data and not isinstance(data['sample'], bool):
        raise ValueError('sample must be a boolean')
    sections = data.get('sections')
    if not isinstance(sections, list) or not sections:
        raise ValueError('sections must be a non-empty list')
    section_ids: set[str] = set()
    block_ids: set[str] = set()
    page_titles = data.get('pdfPageTitles')
    if page_titles is not None:
        string_list(page_titles, 'pdfPageTitles')
    used_pages: list[int] = []
    for section in sections:
        if not isinstance(section, dict):
            raise ValueError('Each section must be an object')
        sid = text_value(section.get('id'), 'section.id')
        if sid in section_ids:
            raise ValueError(f'Duplicate section id: {sid}')
        section_ids.add(sid)
        text_value(section.get('title'), f'{sid}.title')
        text_value(section.get('summary'), f'{sid}.summary', optional=True)
        if not isinstance(section.get('blocks'), list) or not section['blocks']:
            raise ValueError(f'{sid}.blocks must be a non-empty list')
        for block in section['blocks']:
            if not isinstance(block, dict):
                raise ValueError(f'{sid}: each block must be an object')
            bid = text_value(block.get('id'), f'{sid}.block.id')
            if bid in block_ids:
                raise ValueError(f'Duplicate block id: {bid}')
            block_ids.add(bid)
            kind = block.get('type')
            text_value(block.get('hint'), f'{bid}.hint', optional=True)
            if page_titles is not None:
                page = integer(block.get('printPage'), f'{bid}.printPage', 1, len(page_titles))
                used_pages.append(page)
            elif 'printPage' in block:
                raise ValueError(f'{bid}.printPage requires pdfPageTitles')
            if kind == 'definition':
                text_value(block.get('term'), f'{bid}.term')
                text_value(block.get('text'), f'{bid}.text')
            elif kind in ('answer-points', 'bullets', 'steps'):
                text_value(block.get('title'), f'{bid}.title')
                string_list(block.get('items'), f'{bid}.items')
            elif kind == 'comparison':
                text_value(block.get('title'), f'{bid}.title')
                columns = string_list(block.get('columns'), f'{bid}.columns')
                rows = block.get('rows')
                if not isinstance(rows, list) or not rows:
                    raise ValueError(f'{bid}.rows must be a non-empty list')
                for row in rows:
                    string_list(row, f'{bid}.rows[]')
                    if len(row) != len(columns):
                        raise ValueError(f'{bid}: every comparison row must match its column count')
            elif kind == 'example':
                for key in ('title', 'problem', 'result'):
                    text_value(block.get(key), f'{bid}.{key}')
                string_list(block.get('steps'), f'{bid}.steps')
            elif kind == 'equivalence':
                text_value(block.get('title'), f'{bid}.title')
                values = block.get('values')
                if not isinstance(values, list) or len(values) < 2:
                    raise ValueError(f'{bid}.values must contain at least two equivalent representations')
                for value in values:
                    if not isinstance(value, dict):
                        raise ValueError(f'{bid}.values[] must be an object')
                    text_value(value.get('label'), f'{bid}.values[].label')
                    text_value(value.get('value'), f'{bid}.values[].value')
            elif kind == 'callout':
                text_value(block.get('title'), f'{bid}.title')
                text_value(block.get('text'), f'{bid}.text')
            elif kind == 'division':
                text_value(block.get('title'), f'{bid}.title')
                integer(block.get('value'), f'{bid}.value', 0, 65535)
                if block.get('base') not in (2, 16):
                    raise ValueError(f'{bid}.base must be 2 or 16')
            elif kind == 'bit-grid':
                text_value(block.get('title'), f'{bid}.title')
                width = block.get('width')
                if width not in (8, 16):
                    raise ValueError(f'{bid}.width must be 8 or 16')
                weights = block.get('weights')
                if weights is not None and (not isinstance(weights, list) or len(weights) != width
                        or any(isinstance(x, bool) or not isinstance(x, int) for x in weights)):
                    raise ValueError(f'{bid}.weights must match the bit width')
                rows = block.get('rows')
                if not isinstance(rows, list) or not rows:
                    raise ValueError(f'{bid}.rows must be a non-empty list')
                for row in rows:
                    if not isinstance(row, dict):
                        raise ValueError(f'{bid}.rows[] must be an object')
                    text_value(row.get('label'), f'{bid}.rows[].label')
                    bits = text_value(row.get('bits'), f'{bid}.rows[].bits')
                    if len(bits) != width or any(bit not in '01' for bit in bits):
                        raise ValueError(f'{bid}.rows[].bits must be a {width}-bit string')
                text_value(block.get('note'), f'{bid}.note', optional=True)
            elif kind == 'binary-addition':
                text_value(block.get('title'), f'{bid}.title')
                text_value(block.get('explanation'), f'{bid}.explanation')
                if block.get('width') != 8:
                    raise ValueError(f'{bid}.width must be 8')
                for key in ('a', 'b'):
                    integer(block.get(key), f'{bid}.{key}', 0, 255)
            elif kind == 'logical-shift':
                text_value(block.get('title'), f'{bid}.title')
                text_value(block.get('explanation'), f'{bid}.explanation')
                if block.get('width') != 8 or block.get('direction') not in ('left', 'right'):
                    raise ValueError(f'{bid}: logical shifts require width 8 and left/right direction')
                integer(block.get('value'), f'{bid}.value', 0, 255)
                integer(block.get('places'), f'{bid}.places', 1, 8)
            elif kind == 'sampling-diagram':
                text_value(block.get('title'), f'{bid}.title')
                duration = block.get('duration')
                if (isinstance(duration, bool) or not isinstance(duration, (int, float))
                        or not math.isfinite(duration) or duration <= 0):
                    raise ValueError(f'{bid}.duration must be a finite positive number')
                waveform = block.get('waveform')
                if (not isinstance(waveform, list) or len(waveform) < 2
                        or any(isinstance(value, bool) or not isinstance(value, (int, float))
                               or not math.isfinite(value) or not 0 <= value <= 1 for value in waveform)):
                    raise ValueError(f'{bid}.waveform must contain at least two finite amplitudes from 0 to 1')
                panels = block.get('panels')
                if not isinstance(panels, list) or not 1 <= len(panels) <= 3:
                    raise ValueError(f'{bid}.panels must contain one to three panels')
                for panel in panels:
                    if not isinstance(panel, dict):
                        raise ValueError(f'{bid}.panels[] must be an object')
                    text_value(panel.get('label'), f'{bid}.panels[].label')
                    rate = integer(panel.get('sampleRate'), f'{bid}.panels[].sampleRate', 1, 32)
                    integer(panel.get('resolution'), f'{bid}.panels[].resolution', 1, 4)
                    if duration * rate > 32:
                        raise ValueError(f'{bid}: each panel must contain no more than 32 samples')
            else:
                raise ValueError(f'{bid}: unknown knowledge block type {kind!r}')
    if page_titles is not None and (sorted(set(used_pages)) != list(range(1, len(page_titles) + 1))
                                   or used_pages != sorted(used_pages)):
        raise ValueError('printPage values must be sequential, covering every pdfPageTitles page')
    # Deliberately ignore reviewTopics: it is optional webpage-only self-assessment.
    return data


class KnowledgeTable(LongTable):
    """Keep normal rows whole; long rows continue with headers on the next page."""
    def split(self, availWidth, availHeight):
        self._calc(availWidth, availHeight)
        result = self._splitRows(availHeight, doInRowSplit=False)
        if not result:
            first_data = self.repeatRows if isinstance(self.repeatRows, int) else max(self.repeatRows) + 1
            if (first_data < len(self._rowHeights)
                    and self._rowHeights[first_data] > MAX_WHOLE_ROW_HEIGHT
                    and availHeight > 100):
                result = self._splitRows(availHeight, doInRowSplit=True)
        if len(result) > 1:
            return [result[0], PageBreak(), *result[1:]]
        return result


def styles() -> dict[str, ParagraphStyle]:
    body = dict(fontName='ChecklistSans', textColor=INK, fontSize=10.5, leading=15,
                splitLongWords=True, allowWidows=0, allowOrphans=0)
    return {
        'body': ParagraphStyle('Body', **{**body, 'spaceAfter': 7}),
        'term': ParagraphStyle('Term', **{**body, 'fontName': 'ChecklistSansSemibold', 'textColor': NAVY, 'spaceAfter': 2}),
        'kicker': ParagraphStyle('Kicker', **{**body, 'fontName': 'ChecklistSansSemibold', 'fontSize': 8, 'leading': 11, 'textColor': MUTED, 'spaceAfter': 8}),
        'title': ParagraphStyle('Title', **{**body, 'fontName': 'ChecklistSerif', 'fontSize': 29, 'leading': 33, 'textColor': NAVY, 'spaceAfter': 8}),
        'subtitle': ParagraphStyle('Subtitle', **{**body, 'fontSize': 10.5, 'leading': 15, 'textColor': MUTED, 'spaceAfter': 10}),
        'small': ParagraphStyle('Small', **{**body, 'fontSize': 8.8, 'leading': 12, 'textColor': MUTED, 'spaceAfter': 5}),
        'hint': ParagraphStyle('Hint', **{**body, 'fontSize': 9, 'leading': 13, 'textColor': MUTED, 'spaceAfter': 9}),
        'section': ParagraphStyle('Section', **{**body, 'fontName': 'ChecklistSerifSemibold', 'fontSize': 17, 'leading': 22, 'textColor': NAVY, 'spaceBefore': 15, 'spaceAfter': 7}),
        'summary': ParagraphStyle('Summary', **{**body, 'textColor': MUTED, 'spaceAfter': 9}),
        'block': ParagraphStyle('Block', **{**body, 'fontName': 'ChecklistSansSemibold', 'fontSize': 11.2, 'leading': 15, 'textColor': NAVY, 'spaceBefore': 7, 'spaceAfter': 6}),
        'column': ParagraphStyle('Column', **{**body, 'fontName': 'ChecklistSansSemibold', 'fontSize': 9.5, 'leading': 13, 'textColor': NAVY}),
        'cell': ParagraphStyle('Cell', **{**body, 'fontSize': 10.1, 'leading': 14}),
        'number': ParagraphStyle('Number', **{**body, 'fontName': 'ChecklistSansSemibold', 'fontSize': 10, 'leading': 15, 'textColor': NAVY}),
        'bullet': ParagraphStyle('Bullet', **{**body, 'leftIndent': 13, 'firstLineIndent': 0, 'bulletIndent': 1, 'bulletFontName': 'ChecklistSans', 'bulletFontSize': 9, 'spaceAfter': 4}),
        'value': ParagraphStyle('Value', **{**body, 'fontName': 'ChecklistSansSemibold', 'fontSize': 17, 'leading': 22, 'textColor': NAVY, 'alignment': TA_CENTER}),
        'value_label': ParagraphStyle('ValueLabel', **{**body, 'fontSize': 9, 'leading': 12, 'textColor': MUTED, 'alignment': TA_CENTER}),
        'equals': ParagraphStyle('Equals', **{**body, 'fontName': 'ChecklistSerif', 'fontSize': 22, 'leading': 27, 'textColor': MUTED, 'alignment': TA_CENTER}),
        'result': ParagraphStyle('Result', **{**body, 'fontName': 'ChecklistSansSemibold', 'textColor': NAVY, 'spaceBefore': 5, 'spaceAfter': 9}),
    }


def handout_styles() -> dict[str, ParagraphStyle]:
    """A compact, explicitly paginated revision sheet, with a 10 pt body floor."""
    result = styles()
    for name in ('body', 'term', 'summary', 'bullet', 'result'):
        result[name].fontSize = 10
        result[name].leading = 12.6
        result[name].spaceAfter = 3
        result[name].spaceBefore = 0
    for name in ('cell', 'column'):
        result[name].fontSize = 9
        result[name].leading = 11.1
    result['block'].fontSize = 10.7
    result['block'].leading = 13
    result['block'].spaceBefore = 5
    result['block'].spaceAfter = 3
    result['hint'].fontSize = 8.5
    result['hint'].leading = 11
    result['hint'].spaceAfter = 3
    result['small'].spaceAfter = 3
    result['value'].fontSize = 12
    result['value'].leading = 16
    result['value_label'].fontSize = 8.5
    result['value_label'].leading = 11
    result['number'].fontSize = 9
    result['number'].leading = 11.1
    result['compact'] = True
    return result


def binary_digits(value: int, width: int = 8) -> str:
    return f'{value:0{width}b}'


def division_rows(value: int, base: int) -> list[tuple[int, int, int]]:
    rows = []
    dividend = value
    while True:
        quotient, remainder = divmod(dividend, base)
        rows.append((dividend, quotient, remainder))
        if quotient == 0:
            return rows
        dividend = quotient


def addition_carries(a: int, b: int, width: int) -> list[int]:
    """Nine visual columns: carry beyond register, then eight receiving bits."""
    carries = [0] * (width + 1)
    incoming = 0
    for position in range(width - 1, -1, -1):
        shift = width - position - 1
        incoming = (((a >> shift) & 1) + ((b >> shift) & 1) + incoming) // 2
        carries[position] = incoming
    return carries


class BitDiagram(Flowable):
    """Vector bit cells; whole diagrams never split across printed pages."""
    def __init__(self, block: dict):
        super().__init__()
        self.block = block
        self.width = CONTENT_WIDTH
        self.height = 85 if block['type'] == 'binary-addition' else 66

    def draw(self):
        canvas, block = self.canv, self.block
        label_width = 93
        column_width = (CONTENT_WIDTH - label_width) / 9
        start = label_width

        def label(text, y, size=9):
            canvas.setFillColor(MUTED)
            canvas.setFont('ChecklistSans', size)
            canvas.drawString(0, y - 3, text)

        def bitrow(values, y, zero_indices=(), outside=False):
            for i, value in enumerate(values):
                x = start + column_width*i
                canvas.setFillColor(PALE if i in zero_indices else colors.white)
                canvas.setStrokeColor(RULE)
                if i > 0:
                    canvas.rect(x + 1, y - 10, column_width-2, 19, fill=1, stroke=1)
                canvas.setFillColor(NAVY if i > 0 else MUTED)
                canvas.setFont('ChecklistSansSemibold', 11)
                if value:
                    canvas.drawCentredString(x + column_width/2, y - 3, str(value))
            if outside:
                canvas.saveState()
                canvas.setDash(2, 2)
                canvas.setStrokeColor(MUTED)
                canvas.line(start + column_width, y - 11, start + column_width, self.height - 4)
                canvas.restoreState()

        if block['type'] == 'binary-addition':
            a, b = block['a'], block['b']
            carries = addition_carries(a, b, 8)
            y = self.height - 10
            label(f'{a}  (first value)', y)
            bitrow(['', *binary_digits(a)], y)
            label(f'+ {b}', y-22)
            bitrow(['', *binary_digits(b)], y-22)
            label('Carry into column', y-44, 8.5)
            canvas.setFont('ChecklistSans', 8.5)
            canvas.setFillColor(MUTED)
            for i, carry in enumerate(carries):
                if carry:
                    canvas.drawCentredString(start + column_width*(i+.5), y - 47, '1')
            total = binary_digits(a+b, 9)
            label(f'= {a+b}', y-64)
            bitrow([total[0] if total[0] == '1' else '', *total[1:]], y-64, outside=total[0]=='1')
            canvas.setStrokeColor(NAVY)
            canvas.line(start, y-52, CONTENT_WIDTH, y-52)
        else:
            value, places = block['value'], block['places']
            direction = block['direction']
            before = binary_digits(value)
            if direction == 'left':
                after = (before[places:] + '0'*places)
                zeros = range(9-places, 9)
                dropped = before[:places]
                left, right = start + column_width*4, start + column_width*2
            else:
                after = ('0'*places + before[:-places]) if places < 8 else '0'*8
                zeros = range(1, places+1)
                dropped = before[-places:]
                left, right = start + column_width*2, start + column_width*4
            label(f'Before  {value}', 55)
            bitrow(['', *before], 55)
            label(f'After  {int(after, 2)}', 15)
            bitrow(['', *after], 15, zeros)
            canvas.setStrokeColor(NAVY)
            canvas.setFillColor(NAVY)
            canvas.line(left, 35, right, 35)
            sign = 1 if right > left else -1
            path = canvas.beginPath()
            path.moveTo(right,35)
            path.lineTo(right-sign*5,38)
            path.lineTo(right-sign*5,32)
            path.close()
            canvas.drawPath(path, fill=1, stroke=0)
            canvas.setFont('ChecklistSans', 8.5)
            canvas.setFillColor(MUTED)
            canvas.drawString(0, 32, f'{direction.title()} by {places}')
            canvas.drawRightString(CONTENT_WIDTH, 31, f'Dropped: {dropped}  |  shaded: new zeros')


def sampling_points(block: dict, panel: dict) -> list[tuple[float, float]]:
    """Interpolate the shared waveform and quantize samples, excluding the end time."""
    duration, waveform = block['duration'], block['waveform']
    rate, levels = panel['sampleRate'], 2 ** panel['resolution']
    result = []
    for sample in range(math.ceil(duration * rate)):
        time = sample / rate
        position = time / duration * (len(waveform) - 1)
        left = min(math.floor(position), len(waveform) - 2)
        fraction = position - left
        value = waveform[left] * (1 - fraction) + waveform[left + 1] * fraction
        stored = math.floor(value * (levels - 1) + .5) / (levels - 1)
        result.append((time, stored))
    return result


class SamplingDiagram(Flowable):
    """Equal-scale vector panels compare timing and amplitude precision."""
    def __init__(self, block: dict):
        super().__init__()
        self.block = block
        self.width = CONTENT_WIDTH
        self.panel_gap = 12
        self.panel_width = (self.width - self.panel_gap * (len(block['panels']) - 1)) / len(block['panels'])
        label_style = ParagraphStyle('SamplingPanelLabel', fontName='ChecklistSansSemibold',
                                     fontSize=9, leading=10.5, textColor=NAVY, alignment=TA_CENTER)
        self.labels = [Paragraph(markup(panel['label'], 'ChecklistSansSemibold'), label_style)
                       for panel in block['panels']]
        self.label_height = max(label.wrap(self.panel_width, FRAME_HEIGHT)[1] for label in self.labels)
        self.height = 127 + self.label_height

    def draw(self):
        canvas, block = self.canv, self.block
        curve_colour = colors.HexColor('#8096A5')
        sample_colour = colors.HexColor('#193F59')
        graph_bottom, graph_height = 43, 70
        canvas.saveState()
        for index, (panel, label) in enumerate(zip(block['panels'], self.labels)):
            origin = index * (self.panel_width + self.panel_gap)
            graph_left = origin + 26
            graph_width = self.panel_width - 33
            graph_right = graph_left + graph_width
            label.drawOn(canvas, origin, self.height - label.wrap(self.panel_width, FRAME_HEIGHT)[1])
            canvas.setFont('ChecklistSans', 8)
            canvas.setFillColor(MUTED)
            canvas.drawCentredString(origin + self.panel_width / 2, 117,
                                    f'{panel["sampleRate"]} Hz / {panel["resolution"]} bits per sample')

            levels = 2 ** panel['resolution']
            canvas.setLineWidth(.35)
            canvas.setStrokeColor(RULE)
            canvas.setDash(2, 2)
            for level in range(levels):
                y = graph_bottom + graph_height * level / (levels - 1)
                canvas.line(graph_left, y, graph_right, y)
            canvas.setDash()
            canvas.setStrokeColor(MUTED)
            canvas.setLineWidth(.5)
            canvas.line(graph_left, graph_bottom, graph_left, graph_bottom + graph_height)
            canvas.line(graph_left, graph_bottom, graph_right, graph_bottom)
            canvas.setFont('ChecklistSans', 7)
            canvas.setFillColor(MUTED)
            for amplitude in (0, 1):
                canvas.drawRightString(graph_left - 4, graph_bottom + amplitude * graph_height - 2.2,
                                       str(amplitude))
            for fraction in (0, .5, 1):
                x = graph_left + fraction * graph_width
                canvas.line(x, graph_bottom, x, graph_bottom - 2)
                canvas.drawCentredString(x, graph_bottom - 10, f'{fraction * block["duration"]:g}')
            canvas.drawCentredString(graph_left + graph_width / 2, 21, 'Time (s)')
            canvas.saveState()
            canvas.translate(origin + 7, graph_bottom + graph_height / 2)
            canvas.rotate(90)
            canvas.drawCentredString(0, 0, 'Amplitude')
            canvas.restoreState()

            canvas.setStrokeColor(curve_colour)
            canvas.setLineWidth(1.1)
            path = canvas.beginPath()
            for point, amplitude in enumerate(block['waveform']):
                x = graph_left + point / (len(block['waveform']) - 1) * graph_width
                y = graph_bottom + amplitude * graph_height
                if point:
                    path.lineTo(x, y)
                else:
                    path.moveTo(x, y)
            canvas.drawPath(path, stroke=1, fill=0)
            canvas.setStrokeColor(sample_colour)
            canvas.setFillColor(colors.white)
            for time, amplitude in sampling_points(block, panel):
                x = graph_left + time / block['duration'] * graph_width
                y = graph_bottom + amplitude * graph_height
                canvas.setLineWidth(.5)
                canvas.line(x, graph_bottom, x, y)
                canvas.setLineWidth(.9)
                canvas.circle(x, y, 2.1, stroke=1, fill=1)

        canvas.setFont('ChecklistSans', 7.5)
        canvas.setFillColor(MUTED)
        legend_width = 329
        legend_left = (self.width - legend_width) / 2
        canvas.setStrokeColor(curve_colour)
        canvas.setLineWidth(1.1)
        canvas.line(legend_left, 7, legend_left + 16, 7)
        canvas.drawString(legend_left + 21, 4.5, 'Original waveform')
        canvas.setStrokeColor(sample_colour)
        canvas.setFillColor(colors.white)
        canvas.setLineWidth(.9)
        canvas.circle(legend_left + 111, 7, 2.1, stroke=1, fill=1)
        canvas.setFillColor(MUTED)
        canvas.drawString(legend_left + 118, 4.5, 'Stored sample value')
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(.5)
        canvas.setDash(2, 2)
        canvas.line(legend_left + 207, 7, legend_left + 223, 7)
        canvas.drawString(legend_left + 228, 4.5, 'Possible amplitude levels')
        canvas.restoreState()


class FixedKnowledgePage(Flowable):
    """Preflight one designed page and reject overflow instead of hiding it."""
    def __init__(self, flows: list, page_number: int, page_title: str):
        super().__init__()
        self.flows = flows
        self.width = CONTENT_WIDTH
        self.height = measured(flows)
        if self.height > FRAME_HEIGHT:
            raise ValueError(f'PDF page {page_number} ({page_title}) needs {self.height:.1f} pt; '
                             f'available {FRAME_HEIGHT:.1f} pt. Revise layout or content; no extra page was generated.')

    def draw(self):
        y = self.height
        for flowable in self.flows:
            _, height = flowable.wrap(CONTENT_WIDTH, FRAME_HEIGHT)
            y -= flowable.getSpaceBefore() + height
            flowable.drawOn(self.canv, 0, y)
            y -= flowable.getSpaceAfter()


class KnowledgeDocument(BaseDocTemplate):
    def __init__(self, output: Path, data: dict):
        super().__init__(str(output), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                         topMargin=MARGIN, bottomMargin=MARGIN,
                         title=normalized(f"{data['label']} - {data['title']}"),
                         author='IGCSE 0478 Checklist', pageCompression=1,
                         initialFontName='ChecklistSans', lang='en', invariant=1,
                         allowSplitting=1)
        self.checklist_data = data
        frame = Frame(MARGIN, MARGIN + 9*mm, CONTENT_WIDTH, FRAME_HEIGHT,
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id='body')
        self.addPageTemplates(PageTemplate(id='knowledge', frames=[frame], onPage=self.draw_furniture))

    def draw_furniture(self, canvas, doc):
        data = self.checklist_data
        canvas.saveState()
        y = PAGE_HEIGHT - MARGIN - 3*mm
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, y - 4*mm, PAGE_WIDTH-MARGIN, y - 4*mm)
        canvas.setFillColor(NAVY)
        canvas.setFont('ChecklistSansSemibold', 8)
        canvas.drawString(MARGIN, y, 'COMPUTER SCIENCE  /  0478')
        canvas.setFillColor(MUTED)
        canvas.setFont('ChecklistSans', 8)
        canvas.drawRightString(PAGE_WIDTH-MARGIN, y, 'EXAM REVISION')
        fy = MARGIN + 1*mm
        canvas.setStrokeColor(RULE)
        canvas.line(MARGIN, fy + 5*mm, PAGE_WIDTH-MARGIN, fy + 5*mm)
        footer_parts = [data['syllabus'], f"v{data['version']}"]
        if data['label'].upper() != 'SAMPLE':
            footer_parts.insert(0, data['label'])
        if data['id'].startswith('local-review-'):
            footer_parts.insert(0, 'CHAPTER DRAFT - LOCAL REVIEW')
        elif data.get('sample'):
            footer_parts.insert(0, 'SAMPLE - LOCAL REVIEW')
        footer = '  |  '.join(footer_parts)
        fs = ParagraphStyle('Footer', fontName='ChecklistSans', fontSize=7.2, leading=9, textColor=MUTED)
        p = Paragraph(markup(footer), fs)
        p.wrap(CONTENT_WIDTH-50, 24)
        p.drawOn(canvas, MARGIN, fy-1)
        canvas.setFont('ChecklistSans', 7.5)
        canvas.setFillColor(MUTED)
        total = len(data.get('pdfPageTitles', []))
        canvas.drawRightString(PAGE_WIDTH-MARGIN, fy, f'Page {doc.page}' + (f' of {total}' if total else ''))
        canvas.restoreState()


def measured(flowables: list) -> float:
    return sum(f.wrap(CONTENT_WIDTH, FRAME_HEIGHT)[1] + f.getSpaceBefore() + f.getSpaceAfter() for f in flowables)


def table_start(table: KnowledgeTable) -> float:
    table.wrap(CONTENT_WIDTH, FRAME_HEIGHT)
    headers = table.repeatRows if isinstance(table.repeatRows, int) else len(table.repeatRows)
    heights = table._rowHeights
    return sum(heights[:headers]) + min(heights[headers], MAX_WHOLE_ROW_HEIGHT)


def step_table(items: list[str], s: dict) -> KnowledgeTable:
    rows = [[Paragraph(markup(f'{i:02d}', 'ChecklistSansSemibold'), s['number']), Paragraph(markup(item), s['cell'])] for i, item in enumerate(items, 1)]
    table = KnowledgeTable(rows, colWidths=[10*mm, CONTENT_WIDTH-10*mm], hAlign='LEFT', repeatRows=0, splitByRow=1, splitInRow=1)
    table.setStyle(TableStyle([
        ('FONTNAME',(0,0),(-1,-1),'ChecklistSans'), ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),0), ('RIGHTPADDING',(0,0),(-1,-1),5),
        ('TOPPADDING',(0,0),(-1,-1),1 if s.get('compact') else 4), ('BOTTOMPADDING',(0,0),(-1,-1),2 if s.get('compact') else 5),
    ]))
    return table


def block_flowables(block: dict, s: dict) -> tuple[list, float]:
    """Return flowables and the minimum height needed to introduce this block."""
    kind = block['type']
    compact = s.get('compact', False)
    flows: list = []
    heading: list = []
    if kind not in ('definition', 'callout'):
        heading = [Paragraph(markup(block['title'], 'ChecklistSansSemibold'), s['block'])]
    if kind == 'definition':
        term = Paragraph(markup(block['term'], 'ChecklistSansSemibold'), s['term'])
        p = Paragraph(markup(block['text']), s['body'])
        flows = [term, p]
        minimum = measured([term]) + min(measured([p]), 80)
    elif kind in ('answer-points', 'bullets'):
        # Each answer is a separate, unnumbered point beneath its prompt.
        # The shared data supplies the wording; the renderer assigns no marks.
        paragraphs = [Paragraph(markup(item), s['bullet'], bulletText='•') for item in block['items']]
        flows = heading + paragraphs
        minimum = measured(heading) + min(measured(paragraphs[:1]), 80)
    elif kind == 'steps':
        table = step_table(block['items'], s)
        flows = heading + [table, Spacer(1, 2 if compact else 5)]
        minimum = measured(heading) + table_start(table)
    elif kind == 'comparison':
        headers = [Paragraph(markup(column, 'ChecklistSansSemibold'), s['column']) for column in block['columns']]
        rows = [[Paragraph(markup(cell), s['cell']) for cell in row] for row in block['rows']]
        table = KnowledgeTable([headers, *rows], colWidths=[CONTENT_WIDTH/len(headers)]*len(headers), repeatRows=1, hAlign='LEFT', splitByRow=1, splitInRow=1)
        table.setStyle(TableStyle([
            ('FONTNAME',(0,0),(-1,-1),'ChecklistSans'), ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),8), ('RIGHTPADDING',(0,0),(-1,-1),8),
            ('TOPPADDING',(0,0),(-1,-1),3.5 if compact else 7), ('BOTTOMPADDING',(0,0),(-1,-1),3.5 if compact else 7),
            ('BACKGROUND',(0,0),(-1,0),PALE), ('LINEABOVE',(0,0),(-1,0),0.65,RULE),
            ('LINEBELOW',(0,0),(-1,-1),0.4,RULE), ('LINEBEFORE',(1,0),(-1,-1),0.3,RULE),
        ]))
        flows = heading + [table, Spacer(1, 3 if compact else 9)]
        minimum = measured(heading) + table_start(table)
    elif kind == 'example':
        problem = Paragraph(markup(block['problem']), s['body'])
        table = step_table(block['steps'], s)
        result = Paragraph(markup('Result: ', 'ChecklistSansSemibold') + markup(block['result'], 'ChecklistSansSemibold'), s['result'])
        flows = heading + [problem, table, result]
        minimum = measured(heading + [problem]) + table_start(table)
    elif kind == 'equivalence':
        cells: list = []
        widths: list[float] = []
        count = len(block['values'])
        separator_width = min(18, CONTENT_WIDTH / (count * 4))
        value_width = (CONTENT_WIDTH - (count - 1)*separator_width)/count
        for i, value in enumerate(block['values']):
            if i:
                cells.append(Paragraph(markup('=', 'ChecklistSerif'), s['equals']))
                widths.append(separator_width)
            cells.append([Paragraph(markup(value['label']), s['value_label']), Spacer(1, 4), Paragraph(markup(value['value'], 'ChecklistSansSemibold'), s['value'])])
            widths.append(value_width)
        table = KnowledgeTable([cells], colWidths=widths, repeatRows=0, hAlign='LEFT', splitByRow=1, splitInRow=1)
        table.setStyle(TableStyle([
            ('FONTNAME',(0,0),(-1,-1),'ChecklistSans'), ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('BACKGROUND',(0,0),(-1,-1),PALE), ('TOPPADDING',(0,0),(-1,-1),6 if compact else 10),
            ('BOTTOMPADDING',(0,0),(-1,-1),6 if compact else 10), ('LEFTPADDING',(0,0),(-1,-1),5),
            ('RIGHTPADDING',(0,0),(-1,-1),5),
        ]))
        flows = heading + [table, Spacer(1, 3 if compact else 8)]
        minimum = measured(heading) + table_start(table)
    elif kind == 'division':
        rows = division_rows(block['value'], block['base'])
        cell = ParagraphStyle('DivisionCell', parent=s['cell'], alignment=TA_CENTER)
        columns = ['Dividend', 'Divide by', 'Quotient', 'Remainder']
        table_rows = [[Paragraph(markup(label, 'ChecklistSansSemibold'), cell) for label in columns]]
        for dividend, quotient, remainder in rows:
            table_rows.append([Paragraph(markup(str(dividend)), cell), Paragraph(markup(str(block['base'])), cell),
                               Paragraph(markup(str(quotient)), cell), Paragraph(markup('0123456789ABCDEF'[remainder]), cell)])
        table = Table(table_rows, colWidths=[CONTENT_WIDTH*.22]*4, hAlign='LEFT')
        table.setStyle(TableStyle([
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'), ('BACKGROUND',(0,0),(-1,0),PALE),
            ('TOPPADDING',(0,0),(-1,-1),1.6 if compact else 4),
            ('BOTTOMPADDING',(0,0),(-1,-1),1.6 if compact else 4),
            ('LINEBELOW',(0,0),(-1,-1),.35,RULE), ('LINEBEFORE',(1,0),(-1,-1),.3,RULE),
        ]))
        class DivisionArrow(Flowable):
            def __init__(self, inner):
                super().__init__()
                self.inner = inner
                self.width = CONTENT_WIDTH
                self.inner_height = inner.wrap(CONTENT_WIDTH, FRAME_HEIGHT)[1]
                self.height = max(62, self.inner_height)
            def draw(self):
                self.inner.drawOn(self.canv, 0, self.height-self.inner_height)
                x = CONTENT_WIDTH*.915
                bottom, top = 7, self.height - 22
                self.canv.setStrokeColor(NAVY)
                self.canv.setFillColor(NAVY)
                self.canv.line(x,bottom,x,top)
                path = self.canv.beginPath()
                path.moveTo(x,top)
                path.lineTo(x-3,top-5)
                path.lineTo(x+3,top-5)
                path.close()
                self.canv.drawPath(path, fill=1, stroke=0)
                self.canv.saveState()
                self.canv.translate(x+13,bottom)
                self.canv.rotate(90)
                self.canv.setFont('ChecklistSans',8.5)
                self.canv.drawString(0,0,'Read upwards')
                self.canv.restoreState()
        result = ''.join('0123456789ABCDEF'[row[2]] for row in reversed(rows))
        flows = heading + [DivisionArrow(table), Spacer(1, 3), Paragraph(markup(f'Read remainders from bottom to top: {result} (base {block["base"]}).'), s['body'])]
        minimum = measured(flows)
    elif kind == 'bit-grid':
        bitstyle = ParagraphStyle('BitCell', parent=s['cell'], fontSize=9, leading=11, alignment=TA_CENTER)
        weightstyle = ParagraphStyle('WeightCell', parent=bitstyle, fontSize=8.5, leading=10)
        rows = []
        if 'weights' in block:
            rows.append([Paragraph(markup('Weight', 'ChecklistSansSemibold'), s['column']), *[Paragraph(markup(str(w)), weightstyle) for w in block['weights']]])
        for row in block['rows']:
            rows.append([Paragraph(markup(row['label']), s['cell']), *[Paragraph(markup(bit, 'ChecklistSansSemibold'), bitstyle) for bit in row['bits']]])
        label_width = 76 if block['width'] == 8 else 54
        table = Table(rows, colWidths=[label_width, *[(CONTENT_WIDTH-label_width)/block['width']]*block['width']], hAlign='LEFT')
        commands = [('VALIGN',(0,0),(-1,-1),'MIDDLE'), ('GRID',(0,0),(-1,-1),.4,RULE),
                    ('LEFTPADDING',(0,0),(-1,-1),2), ('RIGHTPADDING',(0,0),(-1,-1),2),
                    ('TOPPADDING',(0,0),(-1,-1),4), ('BOTTOMPADDING',(0,0),(-1,-1),4)]
        if 'weights' in block:
            commands.append(('BACKGROUND',(0,0),(-1,0),PALE))
        table.setStyle(TableStyle(commands))
        flows = heading + [table, Spacer(1, 3)]
        if block.get('note'):
            flows.append(Paragraph(markup(block['note']), s['body']))
        minimum = measured(flows)
    elif kind in ('binary-addition', 'logical-shift'):
        flows = heading + [BitDiagram(block), Spacer(1, 4), Paragraph(markup(block['explanation']), s['body'])]
        minimum = measured(flows)
    elif kind == 'sampling-diagram':
        flows = heading + [SamplingDiagram(block), Spacer(1, 3)]
        minimum = measured(flows)
    else:  # callout
        title = Paragraph(markup(block['title'], 'ChecklistSansSemibold'), s['column'])
        text = Paragraph(markup(block['text']), s['body'])
        table = KnowledgeTable([[[title, Spacer(1, 4), text]]], colWidths=[CONTENT_WIDTH], hAlign='LEFT', repeatRows=0, splitByRow=1, splitInRow=1)
        table.setStyle(TableStyle([
            ('FONTNAME',(0,0),(-1,-1),'ChecklistSans'), ('BACKGROUND',(0,0),(-1,-1),PALE),
            ('LINEBEFORE',(0,0),(0,-1),2,NAVY), ('LEFTPADDING',(0,0),(-1,-1),11),
            ('RIGHTPADDING',(0,0),(-1,-1),11), ('TOPPADDING',(0,0),(-1,-1),5 if compact else 9),
            ('BOTTOMPADDING',(0,0),(-1,-1),4 if compact else 7),
        ]))
        flows = [Spacer(1, 2 if compact else 4), table, Spacer(1, 3 if compact else 9)]
        minimum = table_start(table) + 4
    if block.get('hint'):
        flows.append(Paragraph(markup(block['hint']), s['hint']))
    # Preserve a short explanation, worked example, or hint as one reading unit.
    # Longer blocks flow naturally; only their opening is reserved.
    total_height = measured(flows)
    if total_height <= 220:
        minimum = total_height
    return flows, min(minimum, FRAME_HEIGHT)


def render(data: dict, output: Path, fonts: Path) -> None:
    validate(data)
    register_fonts(fonts)
    if data.get('pdfPageTitles'):
        s = handout_styles()
        story = []
        title_style = ParagraphStyle('PageTitle', parent=s['title'], fontSize=24, leading=28, spaceAfter=5)
        all_blocks = [(block, section.get('summary') if index == 0 else None)
                      for section in data['sections'] for index, block in enumerate(section['blocks'])]
        for number, title in enumerate(data['pdfPageTitles'], 1):
            status = 'CHAPTER DRAFT / LOCAL REVIEW' if data['id'].startswith('local-review-') else 'EXAM REVISION'
            flows = [Paragraph(markup(f'{data["label"]}  {data["title"].upper()}   /   {status}', 'ChecklistSansSemibold'), s['kicker']),
                     Paragraph(markup(f'{number:02d}  {title}', 'ChecklistSerif'), title_style)]
            for block, summary in all_blocks:
                if block['printPage'] == number:
                    if summary:
                        flows.append(Paragraph(markup(summary), s['summary']))
                    block_items, _ = block_flowables(block, s)
                    flows.extend(block_items)
            story.append(FixedKnowledgePage(flows, number, title))
            if number < len(data['pdfPageTitles']):
                story.append(PageBreak())
        output.parent.mkdir(parents=True, exist_ok=True)
        KnowledgeDocument(output, data).build(story)
        return
    s = styles()
    is_draft = data['id'].startswith('local-review-')
    status = 'CHAPTER DRAFT / LOCAL REVIEW' if is_draft else 'LOCAL LAYOUT SAMPLE' if data.get('sample') else 'EXAM REVISION'
    story: list = [
        Paragraph(markup(f"{data['label']}   /   {status}", 'ChecklistSansSemibold'), s['kicker']),
        Paragraph(markup(data['title'], 'ChecklistSerif'), s['title']),
    ]
    if data.get('subtitle'):
        story.append(Paragraph(markup(data['subtitle']), s['subtitle']))
    story.append(Paragraph(markup(f"Syllabus {data['syllabus']}  |  Version {data['version']}"), s['small']))
    if is_draft:
        story.append(Paragraph(markup('Local chapter draft for teacher review. Not yet released to students.'), s['small']))
    elif data.get('sample'):
        story.append(Paragraph(markup('A local layout sample. Chapter scope and final content will be confirmed with your teacher.'), s['small']))
    story.append(Spacer(1, 3))
    for section_number, section in enumerate(data['sections'], 1):
        section_header = [Paragraph(markup(f"{section_number:02d}  /  {section['title']}", 'ChecklistSerifSemibold'), s['section'])]
        if section.get('summary'):
            section_header.append(Paragraph(markup(section['summary']), s['summary']))
        blocks = [block_flowables(block, s) for block in section['blocks']]
        story.append(CondPageBreak(min(FRAME_HEIGHT, measured(section_header) + blocks[0][1])))
        story.extend(section_header)
        for flowables, minimum in blocks:
            story.append(CondPageBreak(minimum))
            story.extend(flowables)
    output.parent.mkdir(parents=True, exist_ok=True)
    KnowledgeDocument(output, data).build(story)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Knowledge checklist JSON from the shared content model')
    parser.add_argument('--output', type=Path, required=True, help='Destination PDF file')
    parser.add_argument('--fonts', type=Path, required=True, help='Directory containing the five bundled TTF files')
    args = parser.parse_args()
    try:
        with args.input.open(encoding='utf-8') as stream:
            data = json.load(stream)
        render(data, args.output, args.fonts)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(1, f'PDF generation failed: {exc}\n')
    print(f'Generated {args.output}')


if __name__ == '__main__':
    main()
