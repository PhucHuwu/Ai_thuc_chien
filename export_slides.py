import os
from bs4 import BeautifulSoup
import os
from bs4 import BeautifulSoup
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

def export_slides_to_pdf(output_filename="presentation.pdf"):
    font_config = FontConfiguration()
    base_dir = "presentation"
    slides_dir = os.path.join(base_dir, "slides")
    css_path = os.path.join(base_dir, "css", "style.css")
    
    # Read the main index.html template
    with open(os.path.join(base_dir, "index.html"), "r", encoding="utf-8") as f:
        index_html_content = f.read()

    soup_template = BeautifulSoup(index_html_content, 'html.parser')

    # Remove the navigation div
    navigation_div = soup_template.find("div", class_="navigation")
    if navigation_div:
        navigation_div.decompose()
    
    # Remove the script tag that loads main.js
    script_tag = soup_template.find("script", src="js/main.js")
    if script_tag:
        script_tag.decompose()

    # Find the slider-container to inject slide content
    slider_container = soup_template.find("div", class_="slider-container")
    
    if not slider_container:
        print("Error: Could not find .slider-container in index.html")
        return

    # Clear existing slide placeholders in the template
    for placeholder_slide in slider_container.find_all("div", class_="slide"):
        placeholder_slide.decompose()

    # Load the main CSS file
    with open(css_path, "r", encoding="utf-8") as f:
        main_css = f.read()
    
    # Add CSS for page breaks and to ensure each slide takes a full page
    pdf_specific_css = """
    .slide {
        page-break-after: always;
        height: 100vh !important; /* Ensure each slide takes full viewport height */
        width: 100vw !important; /* Ensure each slide takes full viewport width */
        display: flex !important; /* Make sure all slides are displayed for PDF rendering */
        opacity: 1 !important; /* Make sure all slides are visible for PDF rendering */
    }
    .slide:last-of-type {
        page-break-after: avoid;
    }
    body {
        margin: 0;
        padding: 0;
    }
    """
    
    # WeasyPrint expects a list of CSS objects
    styles = [
        CSS(string=main_css, font_config=font_config),
        CSS(string=pdf_specific_css, font_config=font_config)
    ]

    # Dynamically inject all slide contents into the template
    for i in range(1, 11):  # Assuming slides from slide1.html to slide10.html
        slide_file = os.path.join(slides_dir, f"slide{i}.html")
        if not os.path.exists(slide_file):
            print(f"Warning: Slide file not found: {slide_file}. Skipping.")
            continue

        with open(slide_file, "r", encoding="utf-8") as f:
            slide_content = f.read()

        new_slide_div = soup_template.new_tag("div", class_="slide", id=f"slide{i}")
        new_slide_div.append(BeautifulSoup(slide_content, 'html.parser'))
        slider_container.append(new_slide_div)
    
    # Convert the combined HTML to PDF
    html_doc = HTML(string=str(soup_template), base_url=base_dir)
    
    try:
        html_doc.write_pdf(output_filename, stylesheets=styles, font_config=font_config)
        print(f"Successfully exported all slides to {output_filename}")
    except Exception as e:
        print(f"Error during PDF generation: {e}")

if __name__ == "__main__":
    export_slides_to_pdf()

if __name__ == "__main__":
    export_slides_to_pdf()
