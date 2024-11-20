import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import fitz  # PyMuPDF
import json
import csv
import os
from datetime import datetime

class PDFViewer:
    def add_field_mode(self):
        self.is_adding_field = not self.is_adding_field
        if self.is_adding_field:
            self.add_field_btn.config(text="Cancel Adding Field")
            self.canvas.config(cursor="cross")
        else:
            self.add_field_btn.config(text="Add Input Field")
            self.canvas.config(cursor="")
    
    def start_resize(self, event, window_id, direction):
        self.resize_start = (event.x_root, event.y_root)
        self.initial_width = int(float(self.canvas.itemcget(window_id, 'width')))
        self.initial_height = int(float(self.canvas.itemcget(window_id, 'height')))
        self.current_window_id = window_id
        self.resize_direction = direction
        
    def do_resize(self, event):
        if not hasattr(self, 'resize_start'):
            return
            
        if self.resize_direction == 'width':
            # Calculate width change
            dx = event.x_root - self.resize_start[0]
            new_width = max(100, self.initial_width + dx)
            self.canvas.itemconfig(self.current_window_id, width=new_width)
            
        elif self.resize_direction == 'height':
            # Calculate height change
            dy = event.y_root - self.resize_start[1]
            new_height = max(25, self.initial_height + dy)
            self.canvas.itemconfig(self.current_window_id, height=new_height)
            
            # Adjust font size based on height
            # Find the entry widget for this window
            for field in self.form_fields:
                if field['window_id'] == self.current_window_id:
                    font_size = max(8, int(new_height * 0.6))  # Adjust this multiplier as needed
                    field['entry'].configure(font=('TkDefaultFont', font_size))
                    break
    
    def on_canvas_click(self, event):
        if not self.is_adding_field:
            return
            
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        field_name = simpledialog.askstring("Input", "Enter field name:")
        if not field_name:
            return
        
        # Create frame to hold entry and resize handles
        frame = ttk.Frame(self.canvas)
        
        # Create entry widget with initial font size
        entry = ttk.Entry(frame, font=('TkDefaultFont', 10))
        entry.pack(side='left', fill='both', expand=True, padx=(0, 20))  # Add right padding for width handle
        
        # Create vertical resize handle with fixed size
        width_handle = ttk.Label(frame, text="║", cursor="sb_h_double_arrow", width=2)
        width_handle.place(relx=1.0, rely=0, relheight=1.0, x=-18)  # Place it at fixed position
        
        # Create horizontal resize handle with fixed size
        height_handle = tk.Label(frame, text="═", cursor="sb_v_double_arrow", 
                               bg='lightgray', height=1)
        height_handle.place(relx=0, rely=1.0, relwidth=1.0, y=-2)  # Place it at fixed position
        
        # Create window on canvas
        window_id = self.canvas.create_window(x, y, window=frame, 
                                            anchor='nw', 
                                            width=150,
                                            height=25)
        
        # Bind resize events
        width_handle.bind("<Button-1>", lambda e: self.start_resize(e, window_id, 'width'))
        width_handle.bind("<B1-Motion>", self.do_resize)
        
        height_handle.bind("<Button-1>", lambda e: self.start_resize(e, window_id, 'height'))
        height_handle.bind("<B1-Motion>", self.do_resize)
        
        self.form_fields.append({
            'frame': frame,
            'entry': entry,
            'window_id': window_id,
            'name': field_name
        })
        
        self.add_field_mode()
    
    def save_fields(self):
        fields_data = []
        field_names = []  # For CSV template
        
        for field in self.form_fields:
            coords = self.canvas.coords(field['window_id'])
            size = (
                self.canvas.itemcget(field['window_id'], 'width'),
                self.canvas.itemcget(field['window_id'], 'height')
            )
            
            fields_data.append({
                'name': field['name'],
                'x': coords[0],
                'y': coords[1],
                'width': size[0],
                'height': size[1]
            })
            field_names.append(field['name'])
        
        # Save JSON configuration
        config_file = f"{self.pdf_path}_fields.json"
        with open(config_file, 'w') as f:
            json.dump(fields_data, f, indent=4)
        
        # Create CSV template
        csv_template = f"{self.pdf_path}_template.csv"
        with open(csv_template, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(field_names)  # Header row
            writer.writerow([''] * len(field_names))  # Example empty row
        
        messagebox.showinfo("Success", 
            f"Fields configuration saved!\n\n"
            f"JSON: {config_file}\n"
            f"CSV Template: {csv_template}")
    
    def process_with_csv(self):
        # First select JSON configuration file
        json_path = filedialog.askopenfilename(
            title="Select Field Configuration File",
            filetypes=[("JSON files", "*.json")]
        )
        
        if not json_path:  # User cancelled
            return
            
        try:
            # Load field configuration
            with open(json_path, 'r') as f:
                self.field_config = json.load(f)
            
            # Then select CSV file
            csv_path = filedialog.askopenfilename(
                title="Select CSV Data File",
                filetypes=[("CSV files", "*.csv")]
            )
            
            if not csv_path:  # User cancelled
                return
            
            # Create output directory next to the CSV file
            output_dir = f"{os.path.splitext(csv_path)[0]}_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.process_pdfs(csv_path, output_dir)
            
        except Exception as e:
            self.show_error_dialog(str(e))
    
    def process_pdfs(self, csv_path, output_dir):
        # Validate CSV headers
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            csv_fields = set(reader.fieldnames)
            expected_fields = {field['name'] for field in self.field_config}
            
            if not expected_fields == csv_fields:
                missing = expected_fields - csv_fields
                extra = csv_fields - expected_fields
                raise ValueError(
                    f"CSV fields don't match form fields.\n"
                    f"Missing fields: {missing}\n"
                    f"Extra fields: {extra}"
                )
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Process each row
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, 1):
                output_path = os.path.join(output_dir, f"output_{i}.pdf")
                self.create_filled_pdf(row, output_path)
        
        messagebox.showinfo("Success", 
            f"PDFs have been created in:\n{output_dir}")
    
    def create_filled_pdf(self, data, output_path):
        # Create new PDF with filled data
        doc = fitz.open(self.pdf_path)
        page = doc[0]  # Assuming single page
        
        # Add text for each field
        for field in self.field_config:
            value = data[field['name']]
            if not value:  # Skip empty fields
                continue
            
            # Get field position and size
            x = float(field['x']) / 2  # Adjust for PDF coordinates
            y = float(field['y']) / 2
            width = float(field['width']) / 2
            height = float(field['height']) / 2
            
            # Create the rectangle for text insertion
            rect = fitz.Rect(x, y, x + width, y + height)
            
            try:
                # Insert text with position
                page.insert_text(
                    point=(x, y + (height/2)),  # Center vertically
                    text=str(value),
                    fontsize=height * 0.6
                )
            except Exception as e:
                print(f"Error inserting text at field {field['name']}: {str(e)}")
                # Try alternative method
                try:
                    page.insert_text(
                        point=(x, y),
                        text=str(value),
                        fontsize=12  # Use fixed font size
                    )
                except Exception as e:
                    print(f"Alternative method also failed: {str(e)}")
        
        # Save the new PDF
        doc.save(output_path)
        doc.close()
    
    def display_page(self):
        page = self.doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.photo = ImageTk.PhotoImage(img)
        
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def show_error_dialog(self, error_message):
        """Show error dialog with copy button"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Error")
        dialog.geometry("500x200")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Create frame
        frame = ttk.Frame(dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Add error message in a scrolled text widget
        text = tk.Text(frame, wrap=tk.WORD, height=8)
        text.insert('1.0', str(error_message))
        text.config(state='disabled')  # Make read-only
        text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Add copy button
        def copy_error():
            dialog.clipboard_clear()
            dialog.clipboard_append(str(error_message))
            messagebox.showinfo("Copied", "Error message copied to clipboard!")
            
        copy_btn = ttk.Button(frame, text="Copy Error", command=copy_error)
        copy_btn.pack(side=tk.LEFT, padx=5)
        
        # Add close button
        close_btn = ttk.Button(frame, text="Close", command=dialog.destroy)
        close_btn.pack(side=tk.RIGHT, padx=5)

    def __init__(self, parent, pdf_path):
        self.parent = parent
        self.pdf_path = pdf_path
        self.is_adding_field = False
        self.form_fields = []
        
        # Get the existing toolbar (first child of parent)
        self.toolbar = parent.winfo_children()[0]
        
        # Add buttons to existing toolbar
        self.add_field_btn = ttk.Button(self.toolbar, text="Add Input Field", 
                                       command=self.add_field_mode)
        self.add_field_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = ttk.Button(self.toolbar, text="Save Fields", 
                                  command=self.save_fields)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        self.process_btn = ttk.Button(self.toolbar, text="Process with CSV", 
                                     command=self.process_with_csv)
        self.process_btn.pack(side=tk.LEFT, padx=5)
        
        # Create main frame for PDF viewer
        self.main_frame = ttk.Frame(parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas and scrollbars
        self.canvas_frame = ttk.Frame(self.main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg='white')
        self.scrolly = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, 
                                   command=self.canvas.yview)
        self.scrollx = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, 
                                   command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=self.scrolly.set, 
                            xscrollcommand=self.scrollx.set)
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrolly.grid(row=0, column=1, sticky="ns")
        self.scrollx.grid(row=1, column=0, sticky="ew")
        
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        self.doc = fitz.open(pdf_path)
        self.display_page()
        