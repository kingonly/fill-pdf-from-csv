# Fill PDF from CSV

A Python application that allows users to add input fields on PDF documents and generate multiple PDFs using data from a CSV file.

## Features

- **PDF Form Creation**:
  - Load and display PDF documents
  - Click to place fields
  - Drag fields to reposition them
  - Resize fields using intuitive handles:
    - Vertical handle (║) to adjust width
    - Horizontal handle (═) to adjust height and font size
  - Real-time field testing with live input
  - Name fields for data mapping

- **Data Processing**:
  - Save field configurations to JSON
  - Automatically generate CSV templates
  - Batch process PDFs using CSV data
  - Error handling with copyable error messages

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/fill-pdf-from-csv.git
cd fill-pdf-from-csv
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install PyMuPDF  # For PDF handling
pip install Pillow   # For image processing
```

## Usage

### Adding Form Fields
1. Click "Open PDF Template" to load your template PDF
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

## Output Files
- `your_template_fields.json` - Field configuration file
- `your_template_template.csv` - CSV template for data input
- `your_data_output_TIMESTAMP/` - Generated PDFs, one per CSV row

## Example
Here's a real world example of filling a tax exemption form:
- [PDF](https://drive.google.com/file/d/1BipCLDSQ8vu8KcjNFuka5-yav3xO9SVt/view?usp=drive_link)
- [Fields](https://drive.google.com/file/d/1KWCzxy64hdbj4E-uTu8jWBBcMpiZUkhs/view?usp=drive_link)

## Demo
[![Fill PDF from CSV demo](https://github.com/user-attachments/assets/07ab7592-f235-47a8-8526-67ebdb7ebf25)](https://youtu.be/xOxPaVUNyoU "Fill PDF from CSV demo")

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
