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

    # Find the navigation div and remove it from the template
    navigation_div = soup_template.find("div", class_="navigation")
    if navigation_div:
        navigation_div.decompose()
    
    # Also remove the script tag that loads main.js as it's not needed for static PDF
    script_tag = soup_template.find("script", src="js/main.js")
    if script_tag:
        script_tag.decompose()

    # Find the slider-container to inject slide content
    slider_container = soup_template.find("div", class_="slider-container")
    
    if not slider_container:
        print("Error: Could not find .slider-container in index.html")
        return

    # Load the main CSS file
    with open(css_path, "r", encoding="utf-8") as f:
        main_css = f.read()
    
    # WeasyPrint expects a list of CSS objects
    styles = [CSS(string=main_css, font_config=font_config)]

    # List to hold individual slide PDFs
    all_pages = []

    for i in range(1, 11):  # Assuming slides from slide1.html to slide10.html
        slide_file = os.path.join(slides_dir, f"slide{i}.html")
        if not os.path.exists(slide_file):
            print(f"Warning: Slide file not found: {slide_file}. Skipping.")
            continue

        with open(slide_file, "r", encoding="utf-8") as f:
            slide_content = f.read()

        # Create a new BeautifulSoup object for each slide based on the modified template
        # This ensures each slide is rendered independently without carry-over issues
        current_soup = BeautifulSoup(str(soup_template), 'html.parser')
        current_slider_container = current_soup.find("div", class_="slider-container")

        # Clear existing slide placeholders in the current_slider_container
        for placeholder_slide in current_slider_container.find_all("div", class_="slide"):
            placeholder_slide.decompose()

        # Create a new active slide div and inject content
        new_slide_div = current_soup.new_tag("div", class_="slide active", id=f"slide{i}")
        new_slide_div.append(BeautifulSoup(slide_content, 'html.parser'))
        current_slider_container.append(new_slide_div)

        # Convert the modified HTML to PDF
        html_doc = HTML(string=str(current_soup), base_url=base_dir)
        
        # Render to a temporary PDF and append its pages
        doc = html_doc.render(stylesheets=styles, font_config=font_config)
        all_pages.extend(doc.pages)

    # Combine all pages into a single PDF
    if all_pages:
        doc.copy(all_pages).write_pdf(output_filename)
        print(f"Successfully exported all slides to {output_filename}")
    else:
        print("No slides were processed to create the PDF.")

if __name__ == "__main__":
    export_slides_to_pdf()
