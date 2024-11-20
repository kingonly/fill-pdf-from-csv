import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import fitz
import json
import csv
import os
from PIL import Image, ImageTk
from datetime import datetime

class PDFViewer:
    def __init__(self, parent, pdf_path):
        self.parent = parent
        self.pdf_path = pdf_path
        self.is_adding_field = False
        self.form_fields = []
        self.selected_field = None
        self.resize_mode = None
        
        # Create main frame with no padding
        self.main_frame = ttk.Frame(parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create toolbar with proper padding
        self.toolbar = ttk.Frame(self.main_frame)
        self.toolbar.pack(fill=tk.X, padx=5, pady=8)
        
        # Add toolbar buttons
        self.add_field_btn = ttk.Button(
            self.toolbar, 
            text="Add Input Field", 
            command=self.add_field_mode,
            style='Welcome.TButton'
        )
        self.add_field_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = ttk.Button(
            self.toolbar, 
            text="Save Fields", 
            command=self.save_fields,
            style='Welcome.TButton'
        )
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        self.process_btn = ttk.Button(
            self.toolbar, 
            text="Process with CSV", 
            command=self.process_with_csv,
            style='Welcome.TButton'
        )
        self.process_btn.pack(side=tk.LEFT, padx=5)
        
        # Add status label
        self.status_var = tk.StringVar(value=f"PDF: {os.path.basename(pdf_path)}")
        self.status_label = ttk.Label(
            self.toolbar,
            textvariable=self.status_var,
            font=('Segoe UI', 10),
            foreground='#6c757d'
        )
        self.status_label.pack(side=tk.RIGHT)
        
        # Create canvas frame with no extra padding
        self.canvas_frame = ttk.Frame(self.main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Create canvas and scrollbars
        self.canvas = tk.Canvas(
            self.canvas_frame,
            bg='white',
            highlightthickness=1,
            highlightbackground='#dee2e6'
        )
        
        self.scrolly = ttk.Scrollbar(
            self.canvas_frame,
            orient=tk.VERTICAL,
            command=self.canvas.yview
        )
        self.scrollx = ttk.Scrollbar(
            self.canvas_frame,
            orient=tk.HORIZONTAL,
            command=self.canvas.xview
        )
        
        self.canvas.configure(
            yscrollcommand=self.scrolly.set,
            xscrollcommand=self.scrollx.set
        )
        
        # Grid layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrolly.grid(row=0, column=1, sticky="ns")
        self.scrollx.grid(row=1, column=0, sticky="ew")
        
        # Bind events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Load PDF
        self.doc = fitz.open(pdf_path)
        self.display_page()
        
    def add_field_mode(self):
        """Toggle field addition mode"""
        self.is_adding_field = not self.is_adding_field
        if self.is_adding_field:
            self.status_var.set("Click on PDF to add input field")
        else:
            self.status_var.set(f"PDF: {os.path.basename(self.pdf_path)}")
    
    def save_fields(self):
        """Save field configurations to JSON and create CSV template"""
        if not self.form_fields:
            messagebox.showwarning("No Fields", "No input fields have been added.")
            return
        
        # Get save path for JSON
        json_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile=f"{os.path.splitext(os.path.basename(self.pdf_path))[0]}_fields.json"
        )
        
        if not json_path:
            return
            
        # Save field configurations
        field_config = [
            {
                'name': field['name'],
                'x': field['x'],
                'y': field['y'],
                'width': field['width'],
                'height': field['height'],
                'font_size': field['font_size']
            }
            for field in self.form_fields
        ]
        
        with open(json_path, 'w') as f:
            json.dump(field_config, f, indent=4)
        
        # Create CSV template
        csv_path = os.path.splitext(json_path)[0] + "_template.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([field['name'] for field in self.form_fields])
        
        messagebox.showinfo("Success", 
            f"Field configuration saved to:\n{json_path}\n\n"
            f"CSV template created at:\n{csv_path}")
    
    def process_with_csv(self):
        """Process CSV data to create filled PDFs"""
        # Get JSON configuration
        json_path = filedialog.askopenfilename(
            title="Select Field Configuration",
            filetypes=[("JSON files", "*.json")]
        )
        if not json_path:
            return
            
        # Load field configuration
        with open(json_path, 'r') as f:
            self.field_config = json.load(f)
        
        # Get CSV data file
        csv_path = filedialog.askopenfilename(
            title="Select CSV Data",
            filetypes=[("CSV files", "*.csv")]
        )
        if not csv_path:
            return
        
        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"{os.path.splitext(csv_path)[0]}_output_{timestamp}"
        
        try:
            self.process_pdfs(csv_path, output_dir)
        except Exception as e:
            error_message = str(e)
            messagebox.showerror("Error", 
                f"An error occurred:\n\n{error_message}\n\n"
                "Click OK to copy the error message.",
                parent=self.parent
            )
            self.parent.clipboard_clear()
            self.parent.clipboard_append(error_message)
    
    def process_pdfs(self, csv_path, output_dir):
        """Create PDFs from CSV data"""
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
        """Create a single filled PDF"""
        doc = fitz.open(self.pdf_path)
        page = doc[0]
        
        for field in self.field_config:
            text = data[field['name']]
            rect = fitz.Rect(
                field['x'], 
                field['y'], 
                field['x'] + field['width'], 
                field['y'] + field['height']
            )
            page.insert_text(
                rect.tl,                     # Insert at top-left point
                text,
                fontsize=field['font_size'],
                color=(0, 0, 0),            # Black text
                render_mode=0               # Solid text
            )
        
        doc.save(output_path)
        doc.close()
    
    def display_page(self):
        """Display the first page of PDF"""
        page = self.doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        
        # Calculate desired window size (80% of screen or PDF size, whichever is smaller)
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        
        pdf_width = pix.width
        pdf_height = pix.height
        
        window_width = min(int(screen_width * 0.8), pdf_width + 50)  # Add margin for scrollbars
        window_height = min(int(screen_height * 0.8), pdf_height + 100)  # Add margin for toolbar
        
        # Center the window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Set window size and position
        self.parent.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Display the PDF
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.photo = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        self.canvas.configure(scrollregion=self.canvas.bbox(tk.ALL))
    
    def on_canvas_click(self, event):
        """Handle canvas click events"""
        if self.is_adding_field:
            # Convert screen coordinates to canvas coordinates
            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)
            
            # Create a frame to hold the label and entry
            frame = ttk.Frame(self.canvas)
            frame.place(x=canvas_x, y=canvas_y - 55)  # Moved up to make room for label
            
            # Add help label
            label = ttk.Label(
                frame,
                text="Enter field name:",
                font=('Segoe UI', 10),
                foreground='#2c3e50'
            )
            label.pack(anchor='w', pady=(0, 2))
            
            # Create entry with placeholder
            entry = ttk.Entry(frame, font=('Segoe UI', 11), width=30)
            entry.pack()
            entry.insert(0, "e.g., First Name, Email, Phone...")
            entry.configure(foreground='gray')
            entry.focus_set()
            
            def on_focus_in(event):
                if entry.get() == "e.g., First Name, Email, Phone...":
                    entry.delete(0, tk.END)
                    entry.configure(foreground='black')
            
            def on_focus_out(event):
                if not entry.get():
                    entry.insert(0, "e.g., First Name, Email, Phone...")
                    entry.configure(foreground='gray')
            
            def on_enter(event):
                field_name = entry.get().strip()
                if field_name and field_name != "e.g., First Name, Email, Phone...":
                    frame.destroy()
                    self.add_input_field(canvas_x, canvas_y, field_name)
            
            def on_escape(event):
                frame.destroy()
                self.is_adding_field = False
                self.status_var.set(f"PDF: {os.path.basename(self.pdf_path)}")
            
            # Bind events
            entry.bind('<FocusIn>', on_focus_in)
            entry.bind('<FocusOut>', on_focus_out)
            entry.bind('<Return>', on_enter)
            entry.bind('<Escape>', on_escape)
            
            # Update status
            self.status_var.set("Press Enter to confirm or Escape to cancel")
    
    def add_input_field(self, x, y, field_name):
        """Add new input field at click position"""
        # Create field
        field = {
            'name': field_name,
            'x': x,
            'y': y,
            'width': 100,
            'height': 20,
            'font_size': 11
        }
        
        self.form_fields.append(field)
        self.draw_field(field)
        self.is_adding_field = False
        self.status_var.set(f"PDF: {os.path.basename(self.pdf_path)}")
    
    def draw_field(self, field):
        """Draw input field on canvas"""
        x, y = field['x'], field['y']
        w, h = field['width'], field['height']
        
        # Draw field rectangle
        field['rect'] = self.canvas.create_rectangle(
            x, y, x + w, y + h,
            outline='blue',
            width=2
        )
        
        # Draw field name
        field['label'] = self.canvas.create_text(
            x, y - 10,
            text=field['name'],
            anchor='sw',
            fill='blue'
        )
        
        # Create entry widget with initial font size
        entry = tk.Entry(self.canvas)
        entry.configure(font=('Segoe UI', field['font_size']))
        entry.place(x=x+1, y=y+1, width=w-2, height=h-2)
        field['entry'] = entry
        
        # Draw resize handles
        self.draw_resize_handles(field)
    
    def draw_resize_handles(self, field):
        """Draw handles for resizing the field"""
        x, y = field['x'], field['y']
        w, h = field['width'], field['height']
        
        # Width handle (right edge)
        field['width_handle'] = self.canvas.create_text(
            x + w, y + h/2,
            text="║",
            anchor='w',
            fill='blue',
            tags='handle'
        )
        
        # Height handle (bottom edge)
        field['height_handle'] = self.canvas.create_text(
            x + w/2, y + h,
            text="═",
            anchor='n',
            fill='blue',
            tags='handle'
        )
        
        # Bind events to handles
        self.canvas.tag_bind(field['width_handle'], '<Button-1>', 
            lambda e, f=field: self.start_resize(e, f, 'width'))
        self.canvas.tag_bind(field['height_handle'], '<Button-1>', 
            lambda e, f=field: self.start_resize(e, f, 'height'))
    
    def start_resize(self, event, field, mode):
        """Start resizing a field"""
        self.selected_field = field
        self.resize_mode = mode
        self.start_x = event.x
        self.start_y = event.y
        self.original_width = field['width']
        self.original_height = field['height']
        
        # Bind motion and release events
        self.canvas.bind('<B1-Motion>', self.resize_field)
        self.canvas.bind('<ButtonRelease-1>', self.stop_resize)
        
        # Change cursor based on resize mode
        if mode == 'width':
            self.canvas.configure(cursor='sb_h_double_arrow')
        else:
            self.canvas.configure(cursor='sb_v_double_arrow')
    
    def resize_field(self, event):
        """Resize field while dragging"""
        if not self.selected_field:
            return
            
        if self.resize_mode == 'width':
            # Calculate new width
            delta_x = event.x - self.start_x
            new_width = max(20, self.original_width + delta_x)
            self.selected_field['width'] = new_width
            
        else:  # height mode
            # Calculate new height
            delta_y = event.y - self.start_y
            new_height = max(20, self.original_height + delta_y)
            self.selected_field['height'] = new_height
            
            # Update font size based on height
            new_font_size = int(new_height * 0.55)  # Approximate ratio
            self.selected_field['font_size'] = new_font_size
            
            # Update entry widget font
            self.selected_field['entry'].configure(
                font=('Segoe UI', new_font_size)
            )
        
        # Redraw field
        self.update_field_display(self.selected_field)
    
    def stop_resize(self, event):
        """Stop resizing field"""
        self.selected_field = None
        self.canvas.configure(cursor='')  # Reset cursor
        self.canvas.unbind('<B1-Motion>')
        self.canvas.unbind('<ButtonRelease-1>')
    
    def update_field_display(self, field):
        """Update the display of a field"""
        x, y = field['x'], field['y']
        w, h = field['width'], field['height']
        
        # Update rectangle
        self.canvas.coords(field['rect'], x, y, x + w, y + h)
        
        # Update label
        self.canvas.coords(field['label'], x, y - 10)
        
        # Update entry widget
        field['entry'].place(x=x+1, y=y+1, width=w-2, height=h-2)
        
        # Update resize handles
        self.canvas.coords(field['width_handle'], x + w, y + h/2)
        self.canvas.coords(field['height_handle'], x + w/2, y + h)
