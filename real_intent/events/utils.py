"""Utilities for event generation."""
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

from real_intent.internal_logging import log

from real_intent.events.base import EventsResponse


# ---- PDF ----

def generate_pdf_buffer(self, events_response: EventsResponse) -> BytesIO:
    """
    Generate a PDF file with the events and summary.
    """
    output_buffer = BytesIO()
    c = canvas.Canvas(output_buffer, pagesize=letter)
    width, height = letter

    # background color
    c.setFillColor(colors.aliceblue)
    c.rect(0, 0, width, height, fill=1)  

    title = "Upcoming Local Events"
    title_font_size = 16

    text_width = c.stringWidth(title, "Helvetica-Bold", title_font_size)
    x_position = (width - text_width) / 2  

    # Title
    c.setFillColor(colors.red)
    c.rect(0, height - 50, width, 50, fill=1) 
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", title_font_size)
    c.drawString(x_position, height - 30, title)

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    normal_style.fontName = 'Helvetica'
    normal_style.fontSize = 10
    normal_style.leading = 12

    # Summary
    summary_paragraph = Paragraph(events_response.summary, normal_style)
    paragraph_width = width - 200
    summary_height = summary_paragraph.getSpaceBefore() + summary_paragraph.getSpaceAfter() + summary_paragraph.wrap(paragraph_width, 100)[1]
    summary_paragraph.drawOn(c, 100, height - 60 - summary_height)
    y_position = height - 60 - summary_height - 20

    normal_style = styles['Normal']
    normal_style.fontName = 'Helvetica'
    normal_style.fontSize = 10
    normal_style.leading = 12

    bottom_margin = 70

    for idx, event in enumerate(events_response.events):
        if y_position < bottom_margin:
            log("warning", f"Not all events could fit on the PDF. Truncated at event {idx+1}")
            break

        c.setFillColor(colors.red) 
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, y_position, event.truncated_title)
        y_position -= 20

        c.setFillColor(colors.green) 
        c.setFont("Helvetica", 12)
        c.drawString(100, y_position, f"Date: {event.date}")
        y_position -= 20

        paragraph = Paragraph(event.description, normal_style)
        paragraph_width = width - 200
        paragraph_height = paragraph.getSpaceBefore() + paragraph.getSpaceAfter() + paragraph.wrap(paragraph_width, 100)[1]
        paragraph.drawOn(c, 100, y_position - paragraph_height)
        y_position -= paragraph_height + 20

        c.setFont("Helvetica-Oblique", 10)
        c.setFillColor(colors.blue)
        c.drawString(100, y_position, f"Link: {event.link if event.link else 'N/A'}")
        y_position -= 20

        c.setFillColor(colors.black) 

        c.setStrokeColor(colors.gold)
        c.setLineWidth(1)
        c.line(100, y_position, width - 100, y_position)
        y_position -= 20 

    c.save()

    output_buffer.seek(0)
    return output_buffer
