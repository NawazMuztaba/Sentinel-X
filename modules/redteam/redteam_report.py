#!/usr/bin/env python3
import sys
sys.path.insert(0, "/home/kali/SentinelX")
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import json
import os

def generate_redteam_report(domain, target, exploits):
    filename = f"recon/reports/{domain}_REDTEAM_POC.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=24, spaceAfter=30, alignment=1)
    story.append(Paragraph(f"<b>🔴 RED TEAM PoC - {domain.upper()}</b>", title_style))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph(f"<b>🎯 Primary Target:</b>", styles['Heading2']))
    story.append(Paragraph(f"URL: {target['url']}", styles['Normal']))
    story.append(Paragraph(f"Classification: {target['classification']}", styles['Normal']))
    story.append(Paragraph(f"HTTPS: {'NO ✅ INSECURE' if not target.get('https') else 'YES 🔒'}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph(f"<b>💥 Exploitation Results:</b>", styles['Heading2']))
    total_exploits = 0
    for exploit_type, results in exploits.items():
        if results:
            story.append(Paragraph(f"<b>{exploit_type.replace('_', ' ').title()}:</b>", styles['Heading3']))
            for result in results[:3]:
                story.append(Paragraph(f"• {result}", styles['Normal']))
                total_exploits += 1
        story.append(Spacer(1, 12))
    
    story.append(Paragraph(f"<b>🚨 BUSINESS RISK:</b>", styles['Heading2']))
    risks = [f"HIGH: {target['classification']} compromised", f"{total_exploits} successful exploits", "Immediate remediation required"]
    for risk in risks:
        story.append(Paragraph(risk, styles['Normal']))
    
    doc.build(story)
    print(f"📄 RED TEAM PDF: {filename}")
