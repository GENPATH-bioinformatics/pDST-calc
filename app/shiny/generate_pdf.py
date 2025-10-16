"""
PDF Generation Module for pDST Calculator

This module contains all PDF generation functionality for the pDST Calculator,
including Step 2 and Step 4 PDF reports with comprehensive formatting and styling.
"""

import io
import os
import sys
from datetime import datetime
from math import floor

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

# Add the project root to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from app.api.drug_database import load_drug_data
from lib.dst_calc import potency, est_drugweight, vol_diluent, conc_stock, conc_ws, vol_workingsol, vol_ss_to_ws, calc_volume_difference



def generate_step2_pdf(selected_drugs, make_stock_preference, step2_data):
    """
    Generate PDF for Step 2 calculations with comprehensive formatting.
    
    Args:
        selected_drugs: List of selected drug names
        make_stock_preference: Boolean indicating if stock solutions should be made
        step2_data: Dictionary containing Step 2 calculation results
        
    Returns:
        bytes: PDF content as bytes, or None if generation fails
    """
    try:
        print("generate_step2_pdf: Starting PDF generation")
        
        # Create a bytes buffer for the PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=14,
            spaceAfter=10,
            textColor=colors.darkblue,
            alignment=1  # Center alignment
        )
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=11,
            spaceAfter=10,
            textColor=colors.darkblue,
            alignment=1  # Center alignment
        )
        
        # Load drug data
        drug_data = load_drug_data()
        
        # Build content
        content = []
        
        # Title
        content.append(Paragraph("pDST Calculator - Step 2 Instructions", title_style))
        content.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
        
        # Check if we're making stock solutions
        make_stock = bool(make_stock_preference)
        print(f"generate_step2_pdf: make_stock = {make_stock}")
        
        if make_stock:
            print("generate_step2_pdf: Creating tables for make_stock=True")
            
           # Parameters
            table1_data = [
                ['Drug', 'Crit. Conc.\n(μg/ml)', 'Org. Mol. Wt.\n(g/mol)', 'Purch. Mol. Wt.\n(g/mol)', 'MGIT Tubes']
            ]
            # Calculations
            table2_data = [
                ['Drug','Potency', 'Working Solution\nConcentration\n(μg/ml)', 'Working Solution\nVolume (ml)']
            ]
            # Working Solution Planning
            table3_data = [
                ['Drug', 'Calculated Drug\nWeight (mg)', 'Diluent Volume\n(ml)']
            ]
            # Aliquot Planning
            table4_data = [ 
                ['Drug', 'Number of\nAliquots', 'Volume per\nAliquot (ml)', 'Total Aliquot\nVolume (ml)']
            ]
            # Work Solution Preparation
            table5_data = [ 
                ['Drug', 'Volume of\nStock (ml)', 'Volume Diluent\n(ml)']
            ]
            # Stock Solution Preparation
            table6_data = [ 
                ['Drug', 'Stock Conc.\nIncrease Factor', 'Total Stock\nVolume (ml)', 'Drug to\nWeigh Out\n(mg)']
            ]
            # Actual Weighed Value
            table7_data = [ 
                ['Drug', 'Weighed Value (mg)']
            ]
            
            # Populate tables with data
            for drug_idx, drug_name in enumerate(selected_drugs):
                print(f"generate_step2_pdf: Processing drug {drug_name} at index {drug_idx}")
                
                try:
                    # Table 1: Parameters
                    row = [
                        Paragraph(drug_name, styles['Normal']),
                        f"{step2_data['CriticalConc'][drug_idx]:.2f}",
                        drug_data[drug_data['Drug'] == drug_name].iloc[0]['OrgMolecular_Weight'],
                        f"{step2_data['Purch'][drug_idx]:.2f}",
                        f"{step2_data['MgitTubes'][drug_idx]:.1f}"
                    ]
                    table1_data.append(row)
                    
                    # Table 2: Calculations
                    row = [
                        Paragraph(drug_name, styles['Normal']),
                        f"{step2_data['Potencies'][drug_idx]:.4f}",
                        f"{step2_data['ConcWS'][drug_idx]:.2f}",
                        f"{step2_data['VolWS'][drug_idx]:.2f}"
                    ]
                    table2_data.append(row)
                    
                    # Table 3: Working Solution Planning
                    row = [
                        Paragraph(drug_name, styles['Normal']),
                        f"{step2_data['CalEstWeights'][drug_idx] or 0:.2f}",
                        f"{step2_data['VolWS'][drug_idx]:.2f}"
                    ]
                    table3_data.append(row)
                    
                    # Table 4: Aliquot Planning
                    row = [
                        Paragraph(drug_name, styles['Normal']),
                        f"{step2_data['num_aliquots'][drug_idx] or 0:.1f}",
                        f"{step2_data['mlperAliquot'][drug_idx] or 0:.2f}",
                        f"{step2_data['TotalStockVolumes'][drug_idx] or 0:.2f}"
                    ]
                    table4_data.append(row)
                    
                    # Table 5: Working Solution Preparation
                    row = [
                        Paragraph(drug_name, styles['Normal']),
                        f"{step2_data['StocktoWS'][drug_idx] or 0:.4f}",
                        f"{step2_data['DiltoWS'][drug_idx] or 0:.4f}"
                    ]
                    table5_data.append(row)
                    
                    # Table 6: Stock Solution Preparation
                    row = [ 
                        Paragraph(drug_name, styles['Normal']),
                        f"{step2_data['Factors'][drug_idx] or 0:.2f}",
                        f"{step2_data['TotalStockVolumes'][drug_idx] or 0:.2f}",
                        f"{step2_data['EstWeights'][drug_idx] or 0:.2f}"
                    ]
                    table6_data.append(row)
                    
                    # Table 7: Actual Weighed Value
                    row = [ 
                        Paragraph(drug_name, styles['Normal']),
                        ""
                    ]
                    table7_data.append(row)
                    
                except Exception as e:
                    print(f"generate_step2_pdf: Error processing drug {drug_name}: {e}")
                    continue
        
            # Create and style all tables with proper formatting
            table1 = Table(table1_data, colWidths=[1.8*inch, 1.3*inch, 1.3*inch, 1.3*inch, 1.3*inch])
            table1.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]))

            table2 = Table(table2_data, colWidths=[1.8*inch, 1.3*inch, 1.3*inch, 1.3*inch])
            table2.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]))

            table3 = Table(table3_data, colWidths=[1.8*inch, 1.5*inch, 1.5*inch])
            table3.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]))


            table4 = Table(table4_data, colWidths=[1.8*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            table4.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightyellow),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]))

            table5 = Table(table5_data, colWidths=[1.8*inch, 1.5*inch, 1.5*inch])
            table5.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]))

            table6 = Table(table6_data, colWidths=[1.8*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            table6.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.pink),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]))

            table7 = Table(table7_data, colWidths=[1.8*inch, 1.8*inch])
            table7.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightyellow),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]))

            content.append(Paragraph("Parameters", subtitle_style))
            content.append(table1)
            content.append(Paragraph("Calculations", subtitle_style))
            content.append(table2)
            content.append(Paragraph("Working Solution Planning", subtitle_style))
            content.append(table3)
            content.append(Paragraph("Aliquot Planning", subtitle_style))
            content.append(table4)
            content.append(Paragraph("Work Solution Preparation", subtitle_style))
            content.append(table5)
            content.append(Paragraph("Stock Solution Preparation", subtitle_style))
            content.append(table6)
            content.append(Paragraph("Enter Weighed Value", subtitle_style))
            content.append(table7)
            
            print(f"generate_step2_pdf: Finish content appending for make_stock=True")
        else:
            # Direct dilution pathway
            print("generate_step2_pdf: Creating tables for make_stock=False")
            table1_data = [
                ['Drug', 'Crit. Conc.\n(μg/ml)', 'Org. Mol. Wt.\n(g/mol)', 'Purch. Mol. Wt.\n(g/mol)', 'MGIT Tubes']
            ]
            # Calculations
            table2_data = [
                ['Drug','Potency', 'Working Solution\nConcentration\n(μg/ml)', 'Working Solution\nVolume (ml)']
            ]
            # Working Solution Preparation
            table3_data = [
                ['Drug', 'Est. Drug\nWeight (mg)', 'Diluent Volume\n(ml)']
            ]
            # Practical Weight
            table4_data = [
                ['Drug', 'Practical Weight\nto Weigh Out\n(mg)', 'Diluent Volume\n(ml)']
            ]
            # Actual Weighed Value
            table5_data = [ 
                ['Drug', 'Weighed Value (mg)']
            ]
            for drug_idx, drug_name in enumerate(selected_drugs):
                # Populate direct dilution tables
                row = [
                    Paragraph(drug_name, styles['Normal']),
                    f"{step2_data['CriticalConc'][drug_idx]:.2f}",
                    drug_data[drug_data['Drug'] == drug_name].iloc[0]['OrgMolecular_Weight'],
                    f"{step2_data['Purch'][drug_idx]:.2f}",
                    f"{step2_data['MgitTubes'][drug_idx]:.1f}"
                ]
                table1_data.append(row)
                
                row = [
                    Paragraph(drug_name, styles['Normal']),
                    f"{step2_data['Potencies'][drug_idx]:.4f}",
                    f"{step2_data['ConcWS'][drug_idx]:.2f}",
                    f"{step2_data['VolWS'][drug_idx]:.2f}"
                ]
                table2_data.append(row)
                
                row = [
                    Paragraph(drug_name, styles['Normal']),
                    f"{step2_data['CalEstWeights'][drug_idx]:.2f}",
                    f"{step2_data['VolWS'][drug_idx]:.2f}"
                ]
                table3_data.append(row)
                
                row = [
                    Paragraph(drug_name, styles['Normal']),
                    f"{step2_data['PracWeights'][drug_idx]:.2f}",
                    f"{step2_data['PracVol'][drug_idx]:.4f}"
                ]
                table4_data.append(row)
                
                row = [ 
                    Paragraph(drug_name, styles['Normal']),
                    ""
                ]
                table5_data.append(row)
            
           # Create and style the table
            table1 = Table(table1_data, colWidths=[1.8*inch, 1.3*inch, 1.3*inch, 1.3*inch, 1.3*inch])
            table1.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]))


            table2 = Table(table2_data, colWidths=[1.8*inch, 1.3*inch, 1.3*inch, 1.3*inch])
            table2.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightsteelblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]))


            table3 = Table(table3_data, colWidths=[1.8*inch, 1.5*inch, 1.5*inch])
            table3.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]))


            table4 = Table(table4_data, colWidths=[1.8*inch, 1.5*inch, 1.5*inch])
            table4.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightskyblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]))

            table5 = Table(table5_data, colWidths=[1.8*inch, 1.8*inch])
            table5.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightyellow),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]))
        
            content.append(Paragraph("Parameters", subtitle_style))
            content.append(table1)
            content.append(Paragraph("Calculations", subtitle_style))
            content.append(table2)
            content.append(Paragraph("Working Solution Planning", subtitle_style))
            content.append(table3)
            content.append(Paragraph("Practical Weight", subtitle_style))
            content.append(table4)
            content.append(Paragraph("Enter Weighed Value", subtitle_style))
            content.append(table5)
            
        # Add instructions
        content.append(Paragraph("Instructions:", styles['Heading2']))
        content.append(Paragraph("1. Review the calculated values above", styles['Normal']))
        content.append(Paragraph("2. Ensure all equipment and materials are prepared according to your laboratory protocols", styles['Normal']))
        content.append(Paragraph("3. Weigh out the required amounts of each drug according to above calculations", styles['Normal']))
        content.append(Paragraph("4. Return to this session and enter actual weights in Step 3", styles['Normal']))
            
        # Build PDF
        doc.build(content)
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        print(f"Error generating Step 2 PDF: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_step4_pdf(selected_drugs, make_stock_preference, step2_data, step3_actual_weights, final_results):
    """
    Generate PDF for Step 4 final results with comprehensive formatting.
    
    Args:
        selected_drugs: List of selected drug names
        make_stock_preference: Boolean indicating if stock solutions should be made
        step2_data: Dictionary containing Step 2 calculation results
        step3_actual_weights: List of actual drug weights from Step 3
        final_results: List of final calculation results
        
    Returns:
        bytes: PDF content as bytes, or None if generation fails
    """
    try:
        print("generate_step4_pdf: Starting PDF generation")
        
        # Create a bytes buffer for the PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        # Define styles - matching Step 2 exactly
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=14,
            spaceAfter=10,
            textColor=colors.darkblue,
            alignment=1  # Center alignment
        )
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=11,
            spaceAfter=10,
            textColor=colors.darkblue,
            alignment=1  # Center alignment
        )

        subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=styles['Heading3'],
            fontSize=11,
            spaceAfter=8,
            textColor=colors.black,
            alignment=0  # Left alignment
        )
        
        print(f"generate_step4_pdf: Got final_results: {final_results}")
        
        if not final_results:
            print("generate_step4_pdf: No final results available")
            return None
        
        print(f"generate_step4_pdf: Selected drugs: {selected_drugs}")
            
        # Build content
        content = []
        
        # Title
        content.append(Paragraph("pDST Calculator - Final Results (Step 4)", title_style))
        content.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
        
        # Determine if stock solutions were made
        make_stock = any(result.get('Intermediate') is not None for result in final_results)
        print(f"generate_step4_pdf: make_stock = {make_stock}")

        # Table 1: Stock Solution Calculations
        table1_data = [
            ['Drug', 'Diluent', 'Drug Weight\n(mg)', 'Total Stock\nVolume (ml)', 'Stock\nConcentration\n(μg/ml)', 'Dilution Factor']
        ]
            
        # Table 2: Intermediate Solutions (if any)
        table2_data = [
            ['Drug', 'Diluent', 'Stock to\nAdd (ml)', 'Diluent to\nAdd(ml)', 'Intermediate\nVol. (ml)', 'Intermediate\nConc. (μg/ml)', 'Dilution Factor']
        ]
            
        # Table 3: Working Solution Preparation with inter
        table3_data = [
            ['Drug', 'Diluent', 'Intermediate\nto Add (ml)', 'Diluent to\nAdd (ml)', 'Volume of\nWS (ml)', 'Conc. WS.\n(μg/ml)']
        ]
            
        # Table 4: Working Solution Preparation
        table4_data = [
            ['Drug', 'Diluent', 'Stock to\nAdd (ml)', 'Diluent to\nAdd (ml)', 'Volume of\nWS (ml)', 'Conc. WS.\n(μg/ml)']
        ]

        # Table 5: Working Solution Preparation NO STOCK
        table5_data = [
            ['Drug', 'Diluent', 'Drug Weight\n(mg)', 'Diluent to\nAdd (ml)', 'Volume of\nWS (ml)', 'Conc. WS.\n(μg/ml)']
        ]

        # Table 6: Aliquoting
        table6_data = [
            ['Drug', 'Number of\nAliquots', 'Volume Stock\nper Aliquot (ml)']
        ]

        # Table 7: MGIT Tube Preparation
        table7_data = [
            ['Drug', 'Number of\nMGITs', 'Volume WS per\nMGIT (ml)', 'Volume OADC\n(growth suppl) per\nMGIT (ml)', 'Volume Culture\nper MGIT (ml)']
        ]

        # Load drug data to check for special handling requirements
        drug_data = load_drug_data()

        # Populate tables with data
        for result in final_results:
                drug_name = result.get('Drug', '')
                print(f"generate_step4_pdf: Processing drug {drug_name}")
                
                # Get the actual diluent name from the drug database
                drug_row = drug_data[drug_data['Drug'] == drug_name]
                diluent = drug_row['Diluent'].iloc[0] if not drug_row.empty else 'Unknown'
                
                if make_stock:
                    drug_weight = result.get('Act_Weight', 0) or 0
                    total_stock_vol = result.get('Total_Stock_Vol', 0) or 0
                    stock_conc = result.get('Stock_Conc', 0) or 0
                    dil_factor = result.get('Stock_Factor', 0) or 0
                    
                    row = [
                        Paragraph(drug_name, styles['Normal']),
                        Paragraph(diluent, styles['Normal']),
                        f"{drug_weight:.2f}",
                        f"{total_stock_vol:.2f}",
                        f"{stock_conc:.2f}",
                        f"{dil_factor:.1f}",
                    ]
                    table1_data.append(row)
                
                    # Table 2: Intermediate Solutions (if any)
                    if result.get('Intermediate')  == True:
                        
                        stock_to_add = result.get('Stock_to_Inter', 0) or 0
                        diluent_to_add = result.get('Dil_to_Inter', 0) or 0
                        intermediate_vol = result.get('Dil_to_Inter', 0) or 0
                        intermediate_conc = result.get('Inter_Conc', 0) or 0
                        dil_factor = result.get('Inter_Factor', 0) or 0

                        row = [
                            Paragraph(drug_name, styles['Normal']),
                            Paragraph(diluent, styles['Normal']),
                            f"{stock_to_add:.1f}",
                            f"{diluent_to_add:.4f}",
                            f"{intermediate_vol:.4f}",
                            f"{intermediate_conc:.4f}",
                            f"{dil_factor:.0f}"
                        ]
                        table2_data.append(row)
                        
                        # Table 3: Intermediate WS Solutions (only if intermediate step exists)
                        
                        inter_to_add = result.get('Vol_Inter_to_WS', 0) or 0
                        dil_to_add = result.get('Dil_to_WS', 0) or 0
                        vol_of_ws = result.get('Dil_to_WS', 0) or 0
                        conc_of_ws = result.get('Conc_Ws', 0) or 0
                            
                        row = [
                            Paragraph(drug_name, styles['Normal']),
                            Paragraph(diluent, styles['Normal']),
                            f"{inter_to_add:.2f}",
                            f"{dil_to_add:.4f}",
                            f"{vol_of_ws:.4f}",
                            f"{conc_of_ws:.4f}"
                        ]
                        table3_data.append(row)
                    else:
                    # Table 4: Working Solution Preparation
                        stock_to_add = result.get('Stock_to_WS', 0) or 0
                        diluent_vol = result.get('Dil_to_WS', 0) or 0
                        vol_ws = result.get('Dil_to_WS', 0) or 0
                        ws_conc = result.get('Conc_Ws', 0) or 0
                        
                        row = [
                            Paragraph(drug_name, styles['Normal']),
                            Paragraph(diluent, styles['Normal']),
                            f"{stock_to_add:.4f}",
                            f"{diluent_vol:.4f}",
                            f"{vol_ws:.2f}",
                            f"{ws_conc:.2f}"
                        ]
                        table4_data.append(row)

                    # Table 6: Final Verification (calculate accuracy)
                    num_ali = result.get('Number_of_Ali', 0) or 0
                    ml_ali = result.get('ml_aliquot', 0) or 0

                    row = [
                        Paragraph(drug_name, styles['Normal']),
                        f"{num_ali:.0f}",
                        f"{ml_ali:.1f}"
                    ]
                    table6_data.append(row)


                else:
                    # Table 5: Working Solution Preparation
                        #'Drug', 'Stock to Add\n(ml)', 'Diluent to\nAdd (ml)', 'Volume of WS\n(ml)', 'Conc. WS.\n(μg/ml)'
                        drug_weight = result.get('Act_Weight', 0) or 0
                        diluent_vol = result.get('Final_Vol_Dil', 0) or 0
                        ws_conc = result.get('Conc_Ws', 0) or 0
                        
                        row = [
                            Paragraph(drug_name, styles['Normal']),
                            Paragraph(diluent, styles['Normal']),
                            f"{drug_weight:.4f}",
                            f"{diluent_vol:.4f}",
                            f"{ws_conc:.2f}"
                        ]
                        table5_data.append(row)
                
                # Table 7: Solution Summary
                num_mgit = result.get('MGIT_Tubes', 0) or 0
                vol_per_tube = 0.1
                gro_suppl = 0.8
                culture_vol = 0.5
                
                row = [
                    Paragraph(drug_name, styles['Normal']),
                    f"{num_mgit:.0f}",
                    f"{vol_per_tube:.1f}",
                    f"{gro_suppl:.1f}",
                    f"{culture_vol:.1f}"
                ]
                table7_data.append(row)

            
        table1 = Table(table1_data, colWidths=[1.5*inch, 1.3*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.1*inch])
        table1.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))

        has_intermediate = any(result.get('Intermediate') == True for result in final_results)
            
        table2 = Table(table2_data, colWidths=[1.4*inch, 1.3*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch])
        table2.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightsalmon),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))

        table3 = Table(table3_data, colWidths=[1.5*inch, 1.3*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.1*inch])
        table3.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))
            
        table4 = Table(table4_data, colWidths=[1.5*inch, 1.3*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.1*inch])
        table4.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightcoral),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))

        table6 = Table(table6_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch])
        table6.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightpink),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))

        table5 = Table(table5_data, colWidths=[1.5*inch, 1.3*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.1*inch])
        table5.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightcyan),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))


        table7 = Table(table7_data, colWidths=[1.5*inch, 1.3*inch, 1.3*inch, 1.3*inch, 1.3*inch])
        table7.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightyellow),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))

        
        # Check if any selected drugs require special handling
        bedq = any(result.get('Drug', '') == 'Bedaquiline (BDQ)' for result in final_results)
        dmso = any(
            drug_data[drug_data['Drug'] == result.get('Drug', '')]['Diluent'].iloc[0] == 'DMSO' 
            if not drug_data[drug_data['Drug'] == result.get('Drug', '')].empty else False
            for result in final_results
        )
                    
        content.append(Paragraph("Final Instructions:", subheading_style))
        content.append(Paragraph("1. Review all calculated values below and distinguish between different drugs' workflows", styles['Normal']))
        content.append(Paragraph("2. Follow your laboratory's standard operating procedures for phenotypic drug susceptibility testing", styles['Normal']))
        content.append(Paragraph("3. Ensure proper sterile technique throughout the preparation process", styles['Normal']))
        content.append(Paragraph("4. Label all solutions clearly", styles['Normal']))
        content.append(Paragraph("5. Store solutions according to manufacturer recommendations and laboratory protocols", styles['Normal']))
        content.append(Paragraph("6. Dispose of any unused drug solutions following your institution's hazardous waste disposal guidelines", styles['Normal']))
          
        if bedq:
            content.append(Paragraph("Special Notes for Bedaquiline (BDQ):", subheading_style))
            content.append(Paragraph("Use polystyrene tubes (1.5ml or 5ml) as bedaquiline binds strongly to glass surfaces, which can cause loss of drug and inaccurate (lower) effective concentrations in solution.", styles['Normal']))
            content.append(Paragraph("Do not invert tubes as BDQ will attach to sides, if crystal doesn't dissolve after 1 hour, use sonicator for ~3 minutes", styles['Normal']))

        if dmso:
            content.append(Paragraph("Special Notes for DMSO:", subheading_style))
            content.append(Paragraph("Wrap the tube in foil or use a light-resistant container to protect DMSO from degradation caused by light exposure.", styles['Normal']))
            content.append(Paragraph("", styles['Normal']))

        if make_stock:
            content.append(Paragraph("Stock Solution Preparation", subtitle_style))
            content.append(table1)
            content.append(Paragraph("Preparation Steps:", subheading_style))
            content.append(Paragraph("1. Label a clean container", styles['Normal']))
            content.append(Paragraph("2. Record the drug details:", styles['Normal']))
            content.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;• Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
            content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Drug", styles['Normal']))
            content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Diluent", styles['Normal']))
            content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Concentration", styles['Normal']))
            content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Initials", styles['Normal']))            
            if dmso:
                content.append(Paragraph("3. Wrap the tube in foil or use a light-resistant container to protect DMSO from degradation caused by light exposure.", styles['Normal']))
                content.append(Paragraph("4. Add the weighed drug powder to a clean container", styles['Normal']))
                content.append(Paragraph("5. Add Diluent to the same container", styles['Normal']))
                content.append(Paragraph("6. Mix thoroughly", styles['Normal']))
            else:
                content.append(Paragraph("3. Add the weighed drug powder to a clean container", styles['Normal']))
                content.append(Paragraph("4. Add Diluent to the same container", styles['Normal']))
                content.append(Paragraph("5. Mix thoroughly", styles['Normal']))
            if bedq:
                content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;For bedaquiline: Cap the tube securely. Do not invert tubes as drug will attach to sides. If crystal doesn't dissolve after 1 hour, use sonicator for ~3 minutes", styles['Normal']))
                content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;For other diluents: Cap the tube securely. Invert tube gently 2-4 times or vortex briefly. Do not shake vigorously to avoid foam formation. Check that drug powder is completely dissolved. Ensure no visible particles remain.", styles['Normal']))
            else:    
                content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;Cap the tube securely. Invert tube gently 2-4 times or vortex briefly. Do not shake vigorously to avoid foam formation. Check that drug powder is completely dissolved. Ensure no visible particles remain.", styles['Normal']))

            if has_intermediate:
                content.append(Paragraph("Intermediate Solution Preparation", subtitle_style))
                content.append(table2)
                content.append(Paragraph("Preparation Steps:", subheading_style))
                content.append(Paragraph("1. Label a clean container", styles['Normal']))
                content.append(Paragraph("2. Record the drug details:", styles['Normal']))
                content.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;• Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
                content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Drug", styles['Normal']))
                content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Diluent", styles['Normal']))
                content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Concentration", styles['Normal']))
                content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Initials", styles['Normal']))            
                if dmso:
                    content.append(Paragraph("3. Wrap the tube in foil or use a light-resistant container to protect DMSO from degradation caused by light exposure.", styles['Normal']))
                    content.append(Paragraph("4. Add the weighed drug powder to a clean container", styles['Normal']))
                    content.append(Paragraph("5. Add Diluent to the same container", styles['Normal']))
                    content.append(Paragraph("6. Mix thoroughly", styles['Normal']))
                else:
                    content.append(Paragraph("3. Add the weighed drug powder to a clean container", styles['Normal']))
                    content.append(Paragraph("4. Add Diluent to the same container", styles['Normal']))
                    content.append(Paragraph("5. Mix thoroughly", styles['Normal']))
                if bedq:
                    content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;For bedaquiline: Cap the tube securely. Do not invert tubes as drug will attach to sides. If crystal doesn't dissolve after 1 hour, use sonicator for ~3 minutes", styles['Normal']))
                    content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;For other diluents: Cap the tube securely. Invert tube gently 2-4 times or vortex briefly. Do not shake vigorously to avoid foam formation. Check that drug powder is completely dissolved. Ensure no visible particles remain.", styles['Normal']))
                else:    
                    content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;Cap the tube securely. Invert tube gently 2-4 times or vortex briefly. Do not shake vigorously to avoid foam formation. Check that drug powder is completely dissolved. Ensure no visible particles remain.", styles['Normal']))

                content.append(Paragraph("Working Solution Preparation", subtitle_style))
                content.append(table3)
                content.append(Paragraph("Preparation Steps:", subheading_style))
                content.append(Paragraph("1. Label a clean container", styles['Normal']))
                content.append(Paragraph("2. Record the drug details:", styles['Normal']))
                content.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;• Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
                content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Drug", styles['Normal']))
                content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Diluent", styles['Normal']))
                content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Concentration", styles['Normal']))
                content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Initials", styles['Normal']))            
                if dmso:
                    content.append(Paragraph("3. Wrap the tube in foil or use a light-resistant container to protect DMSO from degradation caused by light exposure.", styles['Normal']))
                    content.append(Paragraph("4. Add the weighed drug powder to a clean container", styles['Normal']))
                    content.append(Paragraph("5. Add Diluent to the same container", styles['Normal']))
                    content.append(Paragraph("6. Mix thoroughly", styles['Normal']))
                else:
                    content.append(Paragraph("3. Add the weighed drug powder to a clean container", styles['Normal']))
                    content.append(Paragraph("4. Add Diluent to the same container", styles['Normal']))
                    content.append(Paragraph("5. Mix thoroughly", styles['Normal']))
                if bedq:
                    content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;For bedaquiline: Cap the tube securely. Do not invert tubes as drug will attach to sides. If crystal doesn't dissolve after 1 hour, use sonicator for ~3 minutes", styles['Normal']))
                    content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;For other diluents: Cap the tube securely. Invert tube gently 2-4 times or vortex briefly. Do not shake vigorously to avoid foam formation. Check that drug powder is completely dissolved. Ensure no visible particles remain.", styles['Normal']))
                else:    
                    content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;Cap the tube securely. Invert tube gently 2-4 times or vortex briefly. Do not shake vigorously to avoid foam formation. Check that drug powder is completely dissolved. Ensure no visible particles remain.", styles['Normal']))
            
            if int(len(table4_data)) > 1:
            
                content.append(Paragraph("Working Solution Preparation", subtitle_style))
                content.append(table4)
                content.append(Paragraph("Preparation Steps:", subheading_style))
                content.append(Paragraph("1. Label a clean container", styles['Normal']))
                content.append(Paragraph("2. Record the drug details:", styles['Normal']))
                content.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;• Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
                content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Drug", styles['Normal']))
                content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Diluent", styles['Normal']))
                content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Concentration", styles['Normal']))
                content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Initials", styles['Normal']))            
                if dmso:
                    content.append(Paragraph("3. Wrap the tube in foil or use a light-resistant container to protect DMSO from degradation caused by light exposure.", styles['Normal']))
                    content.append(Paragraph("4. Add the weighed drug powder to a clean container", styles['Normal']))
                    content.append(Paragraph("5. Add Diluent to the same container", styles['Normal']))
                    content.append(Paragraph("6. Mix thoroughly", styles['Normal']))
                else:
                    content.append(Paragraph("3. Add the weighed drug powder to a clean container", styles['Normal']))
                    content.append(Paragraph("4. Add Diluent to the same container", styles['Normal']))
                    content.append(Paragraph("5. Mix thoroughly", styles['Normal']))
                if bedq:
                    content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;For bedaquiline: Cap the tube securely. Do not invert tubes as drug will attach to sides. If crystal doesn't dissolve after 1 hour, use sonicator for ~3 minutes", styles['Normal']))
                    content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;For other diluents: Cap the tube securely. Invert tube gently 2-4 times or vortex briefly. Do not shake vigorously to avoid foam formation. Check that drug powder is completely dissolved. Ensure no visible particles remain.", styles['Normal']))
                else:    
                    content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;Cap the tube securely. Invert tube gently 2-4 times or vortex briefly. Do not shake vigorously to avoid foam formation. Check that drug powder is completely dissolved. Ensure no visible particles remain.", styles['Normal']))

            content.append(Paragraph("Aliquoting Remaining Stock", subtitle_style))
            content.append(table6)
            content.append(Paragraph("Preparation Steps:", subheading_style))
            content.append(Paragraph("1. Label a clean container", styles['Normal']))
            content.append(Paragraph("2. Record the drug details:", styles['Normal']))
            content.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;• Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
            content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Drug", styles['Normal']))
            content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Diluent", styles['Normal']))
            content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Concentration", styles['Normal']))
            content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Initials", styles['Normal']))
            content.append(Paragraph("3. Add the stock solution to aliquot", styles['Normal']))
            content.append(Paragraph("", styles['Normal']))
            content.append(Paragraph("Special Notes for Aliquots:", subheading_style))
            content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;- Cap tubes tightly and check for proper sealing", styles['Normal']))
            content.append(Paragraph("", styles['Normal']))
            content.append(Paragraph("Storage instructions:", styles['Normal']))
            content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;- Store aliquots at -20°C or -80°C", styles['Normal']))
            content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;- Valid for up to 6 months from preparation date", styles['Normal']))
            content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;- Avoid repeated freeze-thaw cycles", styles['Normal']))
        else:        
            content.append(Paragraph("Working Solution Preparation", subtitle_style))
            content.append(table5)
            content.append(Paragraph("Preparation Steps:", subheading_style))
            content.append(Paragraph("1. Label a clean container", styles['Normal']))
            content.append(Paragraph("2. Record the drug details:", styles['Normal']))
            content.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;• Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
            content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Drug", styles['Normal']))
            content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Diluent", styles['Normal']))
            content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Concentration", styles['Normal']))
            content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Initials", styles['Normal']))            
            if dmso:
                content.append(Paragraph("3. Wrap the tube in foil or use a light-resistant container to protect DMSO from degradation caused by light exposure.", styles['Normal']))
                content.append(Paragraph("4. Add the weighed drug powder to a clean container", styles['Normal']))
                content.append(Paragraph("5. Add Diluent to the same container", styles['Normal']))
                content.append(Paragraph("6. Mix thoroughly", styles['Normal']))
            else:
                content.append(Paragraph("3. Add the weighed drug powder to a clean container", styles['Normal']))
                content.append(Paragraph("4. Add Diluent to the same container", styles['Normal']))
                content.append(Paragraph("5. Mix thoroughly", styles['Normal']))
            if bedq:
                content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;For bedaquiline: Cap the tube securely. Do not invert tubes as drug will attach to sides. If crystal doesn't dissolve after 1 hour, use sonicator for ~3 minutes", styles['Normal']))
                content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;For other diluents: Cap the tube securely. Invert tube gently 2-4 times or vortex briefly. Do not shake vigorously to avoid foam formation. Check that drug powder is completely dissolved. Ensure no visible particles remain.", styles['Normal']))
            else:    
                content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;Cap the tube securely. Invert tube gently 2-4 times or vortex briefly. Do not shake vigorously to avoid foam formation. Check that drug powder is completely dissolved. Ensure no visible particles remain.", styles['Normal']))

        content.append(Paragraph("MGIT Tubes Preparation", subtitle_style))
        content.append(table7)
        content.append(Paragraph("Preparation Steps:", subheading_style))
        content.append(Paragraph("1. Label a clean container", styles['Normal']))
        content.append(Paragraph("2. Record the drug details:", styles['Normal']))
        content.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;• Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
        content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Drug", styles['Normal']))
        content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Diluent", styles['Normal']))
        content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Concentration", styles['Normal']))
        content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;• Initials", styles['Normal']))   
        content.append(Paragraph("For each MGIT tube:", styles['Normal']))
        content.append(Paragraph("3. Pipette 0.1 ml (= 100 µl) of working solution", styles['Normal']))
        content.append(Paragraph("4. Add 0.8 ml (= 800 µl) of OADC (growth supplement)", styles['Normal']))
        content.append(Paragraph("5. Add 0.5 ml (= 500 µl) of culture", styles['Normal']))
        content.append(Paragraph("After adding all components to each tube:", styles['Normal']))
        content.append(Paragraph("6. Mix thoroughly", styles['Normal']))
        if bedq:
            content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;For bedaquiline: Cap the tube securely. Do not invert tubes as drug will attach to sides. If crystal doesn't dissolve after 1 hour, use sonicator for ~3 minutes", styles['Normal']))
            content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;For other diluents: Cap the tube securely. Invert tube gently 2-4 times or vortex briefly. Do not shake vigorously to avoid foam formation. Check that drug powder is completely dissolved. Ensure no visible particles remain.", styles['Normal']))
        else:    
            content.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;Cap the tube securely. Invert tube gently 2-4 times or vortex briefly. Do not shake vigorously to avoid foam formation. Check that drug powder is completely dissolved. Ensure no visible particles remain.", styles['Normal']))

        content.append(Paragraph("7. Place in MGIT machine as soon as possible after adding culture", styles['Normal']))
        print("generate_step4_pdf: Finished content appending for make_stock=True")
  
        # Build PDF
        doc.build(content)
        buffer.seek(0)
        print("generate_step4_pdf: PDF generation completed successfully")
        return buffer.getvalue()
        
    except Exception as e:
        print(f"Error generating Step 4 PDF: {e}")
        import traceback
        traceback.print_exc()
        return None



