# PDF Form Editor

A Python application that allows users to add input fields on PDF documents and generate multiple PDFs using data from a CSV file.

## Features

- Load and display PDF documents
- Add and configure input fields:
  - Click to place fields
  - Resize fields using intuitive handles:
    - Vertical handle (║) to adjust width
    - Horizontal handle (═) to adjust height and font size
  - Name fields for data mapping
- Save field configurations to JSON
- Automatically generate CSV templates
- Batch process PDFs using CSV data
- Error handling with copyable error messages

## Requirements
 bash
 pip install PyMuPDF # For PDF handling
 pip install Pillow # For image processing


## Usage

### Adding Form Fields
1. Click "Open PDF" to load your template PDF
2. Click "Add Input Field" to start placing fields
3. Click on the PDF where you want to place a field
4. Enter a name for the field when prompted
5. Adjust field size using the resize handles:
   - Drag the vertical handle (║) to change width
   - Drag the horizontal handle (═) to change height and font size
6. Click "Save Fields" to store the configuration
   - Creates a JSON file with field configurations
   - Creates a CSV template file

### Generating PDFs
1. Fill out the CSV template with your data
2. Click "Process with CSV"
3. Select your field configuration (JSON file)
4. Select your data file (CSV)
5. PDFs will be generated in a new folder next to your CSV file

## File Structure
- `main.py` - Application entry point
- `pdf_viewer.py` - Main implementation of the PDF viewer and field editor

## Output
- `your_template_fields.json` - Field configuration file
- `your_template_template.csv` - CSV template for data input
- `your_data_output_TIMESTAMP/` - Generated PDFs, one per CSV row