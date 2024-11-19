import tkinter as tk
from tkinter import ttk, simpledialog
from PIL import Image, ImageTk
import fitz  # PyMuPDF
import json

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
        
        config_file = f"{self.pdf_path}_fields.json"
        with open(config_file, 'w') as f:
            json.dump(fields_data, f, indent=4)
        
        print(f"Fields saved to {config_file}")
            
    def display_page(self):
        page = self.doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.photo = ImageTk.PhotoImage(img)
        
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def __init__(self, parent, pdf_path):
        self.parent = parent
        self.pdf_path = pdf_path
        self.is_adding_field = False
        self.form_fields = []
        
        self.main_frame = ttk.Frame(parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.controls = ttk.Frame(self.main_frame)
        self.controls.pack(fill=tk.X)
        
        self.add_field_btn = ttk.Button(self.controls, text="Add Input Field", 
                                       command=self.add_field_mode)
        self.add_field_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = ttk.Button(self.controls, text="Save Fields", 
                                  command=self.save_fields)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
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
        