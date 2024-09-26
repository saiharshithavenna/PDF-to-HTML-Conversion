from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
import pdfplumber
import pdfkit
import os

app = FastAPI()

PDF_UPLOAD_FOLDER = "uploads/"
HTML_OUTPUT_FOLDER = "html_outputs/"
PDF_OUTPUT_FOLDER = "pdf_outputs/"
os.makedirs(PDF_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(HTML_OUTPUT_FOLDER, exist_ok=True)
os.makedirs(PDF_OUTPUT_FOLDER, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Environment(loader=FileSystemLoader("templates"))

#UPLOADING A FILE
@app.get("/", response_class=HTMLResponse)
async def index():
    template = templates.get_template("index.html")
    return HTMLResponse(template.render())

# Handle PDF upload and convert to HTML
@app.post("/upload", response_class=HTMLResponse)
async def upload_pdf(file: UploadFile = File(...)):
    file_path = os.path.join(PDF_UPLOAD_FOLDER, file.filename)
    
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Convert PDF to HTML
    html_content = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            html_content += f"<h2>Page {page.page_number}</h2><div>{page.extract_text()}</div>"

    # Save HTML to a file
    html_file_path = os.path.join(HTML_OUTPUT_FOLDER, file.filename.replace('.pdf', '.html'))
    with open(html_file_path, 'w',encoding='utf-8') as f:
        f.write(html_content)

    template = templates.get_template("edit.html")
    return HTMLResponse(template.render(html_content=html_content, file_name=file.filename))


path_to_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'  # For Windows
config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)

@app.post("/edit")
async def edit_pdf(file_name: str = Form(...), html_content: str = Form(...)):
    html_file_path = os.path.join(HTML_OUTPUT_FOLDER, file_name.replace('.pdf', '.html'))
    pdf_file_path = os.path.join(PDF_OUTPUT_FOLDER, file_name)
    
    # Save the edited HTML content
    with open(html_file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Convert HTML to PDF using pdfkit
    pdfkit.from_file(html_file_path, pdf_file_path, configuration=config)

    return {"message": "PDF saved successfully!", "pdf_file": pdf_file_path}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
