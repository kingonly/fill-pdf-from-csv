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
        self.is_naming_field = False
        self.form_fields = []
        self.selected_field = None
        self.resize_mode = None
        
        # Create main frame with no padding
        self.main_frame = ttk.Frame(parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create toolbar with white background
        self.toolbar = ttk.Frame(self.main_frame)
        self.toolbar.pack(fill=tk.X, padx=5, pady=8)
        
        # Left side: buttons
        self.button_frame = ttk.Frame(self.toolbar)
        self.button_frame.pack(side=tk.LEFT)
        
        self.add_field_btn = ttk.Button(
            self.button_frame, 
            text="Add Input Field", 
            command=self.add_field_mode,
            style='Welcome.TButton'
        )
        self.add_field_btn.pack(side=tk.LEFT, padx=5)
        
        self.load_btn = ttk.Button(
            self.button_frame,
            text="Load Fields",
            command=self.load_fields,
            style='Welcome.TButton'
        )
        self.load_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = ttk.Button(
            self.button_frame, 
            text="Save Fields", 
            command=self.save_fields,
            style='Welcome.TButton'
        )
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        self.process_btn = ttk.Button(
            self.button_frame, 
            text="Process with CSV", 
            command=self.process_with_csv,
            style='Welcome.TButton'
        )
        self.process_btn.pack(side=tk.LEFT, padx=5)
        
        # Add separator between buttons and status
        ttk.Separator(self.toolbar, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=15, pady=5)
        
        # Right side: status/help text with better styling
        self.status_var = tk.StringVar(value=f"Current PDF: {os.path.basename(pdf_path)}")
        self.status_label = ttk.Label(
            self.toolbar,
            textvariable=self.status_var,
            font=('Segoe UI', 11),
            foreground='#2c3e50',
            background='#f8f9fa',
            padding=(10, 5)
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.Y)
        
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
        
        # Configure canvas and scrollbars
        self.canvas.configure(
            yscrollcommand=self.on_vertical_scroll,
            xscrollcommand=self.on_horizontal_scroll
        )
        
        self.scrolly.configure(command=self.canvas.yview)
        self.scrollx.configure(command=self.canvas.xview)
        
        # Bind mouse wheel
        self.canvas.bind('<MouseWheel>', self.on_mousewheel)
        self.canvas.bind('<Shift-MouseWheel>', self.on_shift_mousewheel)
        
        # Grid layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrolly.grid(row=0, column=1, sticky="ns")
        self.scrollx.grid(row=1, column=0, sticky="ew")
        
        # Bind events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Load PDF
        self.doc = fitz.open(pdf_path)
        self.display_page()
        
        # Bind scroll events
        self.canvas.bind('<Configure>', self.on_canvas_scroll)
        self.scrollx.bind('<ButtonRelease-1>', self.on_canvas_scroll)
        self.scrolly.bind('<ButtonRelease-1>', self.on_canvas_scroll)
        self.canvas.bind('<MouseWheel>', self.on_canvas_scroll)
    
    def add_field_mode(self):
        """Toggle field addition mode"""
        if self.is_naming_field:
            return
            
        self.is_adding_field = not self.is_adding_field
        if self.is_adding_field:
            self.status_var.set("👉 Click on PDF to add input field")
        else:
            self.status_var.set(f"Current PDF: {os.path.basename(self.pdf_path)}")
    
    def save_fields(self):
        try:
            print("\nSaving fields:")
            print(f"PDF dimensions: {self.doc[0].rect.width} x {self.doc[0].rect.height}")
            print("-" * 80)
            
            json_path = filedialog.asksaveasfilename(
                defaultextension='.json',
                filetypes=[('JSON files', '*.json')],
                title="Save Field Configuration"
            )
            
            if not json_path:
                return
            
            fields = []
            for field in self.form_fields:
                # Get coordinates of the rectangle (box)
                box_coords = self.canvas.coords(field['rect'])
                box_x = box_coords[0]
                box_y = box_coords[1]
                
                print(f"Field '{field['name']}': "
                      f"Box coordinates ({box_x}, {box_y})")
                
                fields.append({
                    'name': field['name'],
                    'x': box_x,
                    'y': box_y,
                    'width': field['width'],
                    'height': field['height'],
                    'font_size': field['font_size']
                })
            
            with open(json_path, 'w') as f:
                json.dump(fields, f, indent=4)
            
            self.status_var.set(f"✅ Saved {len(fields)} fields to {os.path.basename(json_path)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save fields:\n{str(e)}")
            self.status_var.set("❌ Failed to save fields")
    
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
        
        print("\nRendering PDF:")
        print(f"PDF dimensions: {doc[0].rect.width} x {doc[0].rect.height}")
        print("-" * 80)
        
        for field in self.field_config:
            text = data[field['name']]
            
            # Scale coordinates
            render_x = field['x'] / 2
            render_y = field['y'] / 2
            
            # Calculate baseline position (about 80% down from the top of the field)
            baseline_offset = (field['height'] / 2) * 0.8
            render_y += baseline_offset
            
            print(f"Field '{field['name']}': "
                  f"Original({field['x']}, {field['y']}) -> "
                  f"Rendered({render_x}, {render_y})")
            
            rect = fitz.Rect(
                render_x, 
                render_y, 
                render_x + (field['width'] / 2), 
                render_y + (field['height'] / 2)
            )
            page.insert_text(
                rect.tl,
                text,
                fontsize=field['font_size'],
                color=(0, 0, 0),
                render_mode=0
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
        if self.is_adding_field and not self.is_naming_field:
            # Convert screen coordinates to canvas coordinates
            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)
            
            # Get scroll position
            scroll_x = self.canvas.canvasx(0)
            scroll_y = self.canvas.canvasy(0)
            
            # Set naming state
            self.is_naming_field = True
            
            # Create a frame to hold the label and entry
            frame = ttk.Frame(self.canvas)
            frame.place(
                x=canvas_x - scroll_x,  # Adjust for scroll position
                y=canvas_y - scroll_y - 55  # Adjust for scroll position and offset
            )
            
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
                    self.is_naming_field = False
                    self.add_input_field(canvas_x, canvas_y, field_name)
            
            def on_escape(event):
                frame.destroy()
                self.is_naming_field = False
                self.is_adding_field = False
                self.status_var.set(f"PDF: {os.path.basename(self.pdf_path)}")
            
            # Bind events
            entry.bind('<FocusIn>', on_focus_in)
            entry.bind('<FocusOut>', on_focus_out)
            entry.bind('<Return>', on_enter)
            entry.bind('<Escape>', on_escape)
            
            # Store frame reference to update position during scroll
            self.naming_frame = frame
            self.naming_field_pos = (canvas_x, canvas_y)
            
            # Update status
            self.status_var.set("✏️ Enter field name and press Enter to confirm")
    
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
        self.status_var.set(f"Current PDF: {os.path.basename(self.pdf_path)}")
    
    def draw_field(self, field):
        """Draw input field on canvas"""
        x, y = field['x'], field['y']
        w, h = field['width'], field['height']
        
        # Draw field rectangle at the loaded coordinates
        field['rect'] = self.canvas.create_rectangle(
            x, y, x + w, y + h,
            outline='blue',
            width=2
        )
        
        # Draw field name label ABOVE the rectangle
        field['label'] = self.canvas.create_text(
            x, y - 10,  # Position label above the box
            text=field['name'],
            anchor='sw',
            fill='blue',
            tags='draggable'
        )
        
        # Create entry widget
        entry = tk.Entry(self.canvas)
        entry.configure(font=('Segoe UI', field['font_size']))
        entry.place(x=x+1, y=y+1, width=w-2, height=h-2)
        field['entry'] = entry
        
        # Draw resize handles
        self.draw_resize_handles(field)
        
        # Bind events
        self.canvas.tag_bind(field['label'], '<Button-1>', 
            lambda e, f=field: self.start_drag(e, f))
        self.canvas.tag_bind(field['label'], '<B1-Motion>', 
            lambda e, f=field: self.drag_field(e, f))
        self.canvas.tag_bind(field['label'], '<ButtonRelease-1>', 
            lambda e, f=field: self.stop_drag(e, f))
    
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
        self.canvas.tag_bind(field['width_handle'], '<Enter>', 
            lambda e: self.canvas.configure(cursor='sb_h_double_arrow'))
        self.canvas.tag_bind(field['width_handle'], '<Leave>', 
            lambda e: self.canvas.configure(cursor=''))
        self.canvas.tag_bind(field['width_handle'], '<Button-1>', 
            lambda e, f=field: self.start_resize(e, f, 'width'))
            
        self.canvas.tag_bind(field['height_handle'], '<Enter>', 
            lambda e: self.canvas.configure(cursor='sb_v_double_arrow'))
        self.canvas.tag_bind(field['height_handle'], '<Leave>', 
            lambda e: self.canvas.configure(cursor=''))
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
    
    def start_drag(self, event, field):
        """Start dragging a field"""
        # Store initial coordinates
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.field_start_x = field['x']
        self.field_start_y = field['y']
        # Change cursor to indicate dragging
        self.canvas.configure(cursor='fleur')
    
    def drag_field(self, event, field):
        """Move field while dragging"""
        # Calculate movement delta
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        
        # Update field position
        new_x = self.field_start_x + dx
        new_y = self.field_start_y + dy
        
        # Update field coordinates
        field['x'] = new_x
        field['y'] = new_y
        
        # Update display
        self.update_field_display(field)
    
    def stop_drag(self, event, field):
        """Stop dragging a field"""
        # Reset cursor
        self.canvas.configure(cursor='')
    
    def update_field_display(self, field):
        """Update the display of a field"""
        x, y = field['x'], field['y']
        w, h = field['width'], field['height']
        
        # Get canvas scroll position
        scroll_x = self.canvas.canvasx(0)
        scroll_y = self.canvas.canvasy(0)
        
        # Update rectangle
        self.canvas.coords(field['rect'], x, y, x + w, y + h)
        
        # Update label
        self.canvas.coords(field['label'], x, y - 10)
        
        # Update entry widget with scroll offset
        field['entry'].place(
            x=x - scroll_x + 1,
            y=y - scroll_y + 1,
            width=w-2,
            height=h-2
        )
        
        # Update resize handles
        self.canvas.coords(field['width_handle'], x + w, y + h/2)
        self.canvas.coords(field['height_handle'], x + w/2, y + h)
    
    def on_canvas_scroll(self, *args):
        """Handle canvas scroll events"""
        # Update all field positions
        for field in self.form_fields:
            self.update_field_display(field)
    
    def load_fields(self):
        """Load field configuration from JSON"""
        json_path = filedialog.askopenfilename(
            title="Select Field Configuration",
            filetypes=[("JSON files", "*.json")]
        )
        
        if not json_path:
            return
            
        try:
            # Load field configuration
            with open(json_path, 'r') as f:
                fields = json.load(f)
            
            # Clear existing fields
            for field in self.form_fields:
                if 'entry' in field:
                    field['entry'].destroy()
                self.canvas.delete(field['rect'])
                self.canvas.delete(field['label'])
                if 'width_handle' in field:
                    self.canvas.delete(field['width_handle'])
                if 'height_handle' in field:
                    self.canvas.delete(field['height_handle'])
            
            # Reset form fields list
            self.form_fields = []
            
            # Create fields from configuration
            for field_config in fields:
                field = {
                    'name': field_config['name'],
                    'x': field_config['x'],
                    'y': field_config['y'],
                    'width': field_config['width'],
                    'height': field_config['height'],
                    'font_size': field_config['font_size']
                }
                self.form_fields.append(field)
                self.draw_field(field)
            
            self.status_var.set(f"✅ Loaded {len(fields)} fields from {os.path.basename(json_path)}")
            
        except Exception as e:
            messagebox.showerror("Error", 
                f"Failed to load fields:\n{str(e)}")
            self.status_var.set("❌ Failed to load fields")
    
    def on_vertical_scroll(self, *args):
        """Handle vertical scrolling"""
        self.scrolly.set(*args)
        self.update_all_fields()
    
    def on_horizontal_scroll(self, *args):
        """Handle horizontal scrolling"""
        self.scrollx.set(*args)
        self.update_all_fields()
    
    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.update_all_fields()
    
    def on_shift_mousewheel(self, event):
        """Handle horizontal mouse wheel scrolling"""
        self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
        self.update_all_fields()
    
    def update_all_fields(self):
        """Update all field positions"""
        for field in self.form_fields:
            self.update_field_display(field)
