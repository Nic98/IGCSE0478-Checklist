#!/usr/bin/env python3
"""Render shared knowledge-checklist JSON as a complete, static A4 handout.

All text is treated as plain text. All fonts are provided by --fonts, so builds
work without system fonts or a network connection. Optional reviewTopics are a web-only supplement. No self-assessment table,
selection, interactive form field, or review topic is rendered in the PDF.
"""
from __future__ import annotations

import argparse
import json
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
    Spacer, Table, TableStyle,
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
            if kind == 'definition':
                text_value(block.get('term'), f'{bid}.term')
                text_value(block.get('text'), f'{bid}.text')
            elif kind in ('bullets', 'steps'):
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
            else:
                raise ValueError(f'{bid}: unknown knowledge block type {kind!r}')
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
        canvas.drawRightString(PAGE_WIDTH-MARGIN, y, 'KNOWLEDGE CHECKLIST')
        fy = MARGIN + 1*mm
        canvas.setStrokeColor(RULE)
        canvas.line(MARGIN, fy + 5*mm, PAGE_WIDTH-MARGIN, fy + 5*mm)
        footer_parts = [data['syllabus'], f"v{data['version']}"]
        if data['label'].upper() != 'SAMPLE':
            footer_parts.insert(0, data['label'])
        if data.get('sample'):
            footer_parts.insert(0, 'SAMPLE - LOCAL REVIEW')
        footer = '  |  '.join(footer_parts)
        fs = ParagraphStyle('Footer', fontName='ChecklistSans', fontSize=7.2, leading=9, textColor=MUTED)
        p = Paragraph(markup(footer), fs)
        p.wrap(CONTENT_WIDTH-50, 24)
        p.drawOn(canvas, MARGIN, fy-1)
        canvas.setFont('ChecklistSans', 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawRightString(PAGE_WIDTH-MARGIN, fy, f'Page {doc.page}')
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
        ('TOPPADDING',(0,0),(-1,-1),4), ('BOTTOMPADDING',(0,0),(-1,-1),5),
    ]))
    return table


def block_flowables(block: dict, s: dict) -> tuple[list, float]:
    """Return flowables and the minimum height needed to introduce this block."""
    kind = block['type']
    flows: list = []
    heading: list = []
    if kind not in ('definition', 'callout'):
        heading = [Paragraph(markup(block['title'], 'ChecklistSansSemibold'), s['block'])]
    if kind == 'definition':
        term = Paragraph(markup(block['term'], 'ChecklistSansSemibold'), s['term'])
        p = Paragraph(markup(block['text']), s['body'])
        flows = [term, p]
        minimum = measured([term]) + min(measured([p]), 80)
    elif kind == 'bullets':
        paragraphs = [Paragraph(markup(item), s['bullet'], bulletText='•') for item in block['items']]
        flows = heading + paragraphs
        minimum = measured(heading) + min(measured(paragraphs[:1]), 80)
    elif kind == 'steps':
        table = step_table(block['items'], s)
        flows = heading + [table, Spacer(1, 5)]
        minimum = measured(heading) + table_start(table)
    elif kind == 'comparison':
        headers = [Paragraph(markup(column, 'ChecklistSansSemibold'), s['column']) for column in block['columns']]
        rows = [[Paragraph(markup(cell), s['cell']) for cell in row] for row in block['rows']]
        table = KnowledgeTable([headers, *rows], colWidths=[CONTENT_WIDTH/len(headers)]*len(headers), repeatRows=1, hAlign='LEFT', splitByRow=1, splitInRow=1)
        table.setStyle(TableStyle([
            ('FONTNAME',(0,0),(-1,-1),'ChecklistSans'), ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),8), ('RIGHTPADDING',(0,0),(-1,-1),8),
            ('TOPPADDING',(0,0),(-1,-1),7), ('BOTTOMPADDING',(0,0),(-1,-1),7),
            ('BACKGROUND',(0,0),(-1,0),PALE), ('LINEABOVE',(0,0),(-1,0),0.65,RULE),
            ('LINEBELOW',(0,0),(-1,-1),0.4,RULE), ('LINEBEFORE',(1,0),(-1,-1),0.3,RULE),
        ]))
        flows = heading + [table, Spacer(1, 9)]
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
            ('BACKGROUND',(0,0),(-1,-1),PALE), ('TOPPADDING',(0,0),(-1,-1),10),
            ('BOTTOMPADDING',(0,0),(-1,-1),10), ('LEFTPADDING',(0,0),(-1,-1),5),
            ('RIGHTPADDING',(0,0),(-1,-1),5),
        ]))
        flows = heading + [table, Spacer(1, 8)]
        minimum = measured(heading) + table_start(table)
    else:  # callout
        title = Paragraph(markup(block['title'], 'ChecklistSansSemibold'), s['column'])
        text = Paragraph(markup(block['text']), s['body'])
        table = KnowledgeTable([[[title, Spacer(1, 4), text]]], colWidths=[CONTENT_WIDTH], hAlign='LEFT', repeatRows=0, splitByRow=1, splitInRow=1)
        table.setStyle(TableStyle([
            ('FONTNAME',(0,0),(-1,-1),'ChecklistSans'), ('BACKGROUND',(0,0),(-1,-1),PALE),
            ('LINEBEFORE',(0,0),(0,-1),2,NAVY), ('LEFTPADDING',(0,0),(-1,-1),11),
            ('RIGHTPADDING',(0,0),(-1,-1),11), ('TOPPADDING',(0,0),(-1,-1),9),
            ('BOTTOMPADDING',(0,0),(-1,-1),7),
        ]))
        flows = [Spacer(1, 4), table, Spacer(1, 9)]
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
    s = styles()
    status = 'LOCAL LAYOUT SAMPLE' if data.get('sample') else 'KNOWLEDGE CHECKLIST'
    story: list = [
        Paragraph(markup(f"{data['label']}   /   {status}", 'ChecklistSansSemibold'), s['kicker']),
        Paragraph(markup(data['title'], 'ChecklistSerif'), s['title']),
    ]
    if data.get('subtitle'):
        story.append(Paragraph(markup(data['subtitle']), s['subtitle']))
    story.append(Paragraph(markup(f"Syllabus {data['syllabus']}  |  Version {data['version']}"), s['small']))
    if data.get('sample'):
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
