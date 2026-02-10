# OUTILS PDF

def merge_pdfs(files, form_data=None):
    """Fusionne plusieurs PDF."""
    try:
        pdf_writer = PyPDF2.PdfWriter()
        
        for file in files:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Ajouter toutes les pages
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                pdf_writer.add_page(page)
        
        # Écrire le PDF fusionné
        output = BytesIO()
        pdf_writer.write(output)
        output.seek(0)
        
        filename = f"fusionne_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(output,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/pdf')
        
    except Exception as e:
        current_app.logger.error(f"Erreur fusion PDF: {str(e)}")
        return {'error': f'Erreur de fusion: {str(e)}'}


def split_pdf(file, form_data=None):
    """Divise un PDF."""
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        num_pages = len(pdf_reader.pages)
        
        # Obtenir les plages de pages
        ranges = form_data.get('ranges', 'all') if form_data else 'all'
        
        if ranges == 'all':
            # Diviser chaque page
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for i in range(num_pages):
                    pdf_writer = PyPDF2.PdfWriter()
                    pdf_writer.add_page(pdf_reader.pages[i])
                    
                    page_buffer = BytesIO()
                    pdf_writer.write(page_buffer)
                    page_buffer.seek(0)
                    
                    filename = f"page_{i+1:03d}.pdf"
                    zip_file.writestr(filename, page_buffer.getvalue())
            
            zip_buffer.seek(0)
            
            filename = f"{os.path.splitext(file.filename)[0]}_pages.zip"
            
            return send_file(zip_buffer,
                            as_attachment=True,
                            download_name=filename,
                            mimetype='application/zip')
        else:
            # Diviser selon les plages spécifiées
            return {'error': 'Division par plages non implémentée'}
        
    except Exception as e:
        current_app.logger.error(f"Erreur division PDF: {str(e)}")
        return {'error': f'Erreur de division: {str(e)}'}


def compress_pdf(file, form_data=None):
    """Compresse un PDF."""
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        pdf_writer = PyPDF2.PdfWriter()
        
        # Copier toutes les pages (compression basique)
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        
        # Options de compression
        compress_level = int(form_data.get('level', 1)) if form_data else 1
        
        # Écrire avec compression
        output = BytesIO()
        pdf_writer.write(output)
        
        # Réduire la taille (méthode simple)
        if compress_level > 1:
            # Ré-écrire avec des options de compression
            pass
        
        output.seek(0)
        
        filename = f"{os.path.splitext(file.filename)[0]}_compresse.pdf"
        
        return send_file(output,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/pdf')
        
    except Exception as e:
        current_app.logger.error(f"Erreur compression PDF: {str(e)}")
        return {'error': f'Erreur de compression: {str(e)}'}


def rotate_pdf(file, form_data=None):
    """Tourne les pages d'un PDF."""
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        pdf_writer = PyPDF2.PdfWriter()
        
        # Angle de rotation
        angle = int(form_data.get('angle', 90)) if form_data else 90
        
        # Tourner chaque page
        for page in pdf_reader.pages:
            page.rotate(angle)
            pdf_writer.add_page(page)
        
        # Écrire le PDF
        output = BytesIO()
        pdf_writer.write(output)
        output.seek(0)
        
        filename = f"{os.path.splitext(file.filename)[0]}_rotation.pdf"
        
        return send_file(output,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/pdf')
        
    except Exception as e:
        current_app.logger.error(f"Erreur rotation PDF: {str(e)}")
        return {'error': f'Erreur de rotation: {str(e)}'}