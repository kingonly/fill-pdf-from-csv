import tkinter as tk
from tkinter import ttk, filedialog
from pdf_viewer import PDFViewer

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Fill PDF from CSV")
        self.root.minsize(600, 400)
        self.root.configure(bg='#ffffff')
        
        # Configure styles
        style = ttk.Style()
        style.configure('Welcome.TLabel', 
                       font=('Segoe UI', 24, 'bold'),
                       foreground='#2c3e50')
        style.configure('Instruction.TLabel', 
                       font=('Segoe UI', 12),
                       foreground='#34495e',
                       wraplength=500,
                       justify='center')
        style.configure('Welcome.TButton', 
                       font=('Segoe UI', 11),
                       padding=10)
        
        # Create main container
        self.main_container = ttk.Frame(root, padding="40")
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create welcome screen
        self.welcome_frame = ttk.Frame(self.main_container)
        self.welcome_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Add welcome message
        self.welcome_label = ttk.Label(
            self.welcome_frame,
            text="Fill PDF from CSV",
            style='Welcome.TLabel'
        )
        self.welcome_label.pack(pady=(0, 30))
        
        # Add instructions
        self.instruction_label = ttk.Label(
            self.welcome_frame,
            text="Create a template by adding input fields to your PDF document. "
                 "Save the configuration and use a CSV file to generate multiple PDFs with different values.",
            style='Instruction.TLabel'
        )
        self.instruction_label.pack(pady=(0, 30))
        
        # Add button
        self.button_frame = ttk.Frame(self.welcome_frame)
        self.button_frame.pack(pady=10)
        
        self.open_btn = ttk.Button(
            self.button_frame,
            text="Open PDF Template",
            command=self.open_pdf,
            style='Welcome.TButton'
        )
        self.open_btn.pack()
    
    def open_pdf(self):
        pdf_path = filedialog.askopenfilename(
            title="Select PDF Template",
            filetypes=[("PDF files", "*.pdf")]
        )
        
        if pdf_path:
            self.main_container.pack_forget()
            self.welcome_frame.destroy()
            
            self.viewer = PDFViewer(self.root, pdf_path)

def main():
    root = tk.Tk()
    
    # Center window on screen
    window_width = 800
    window_height = 600
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width/2 - window_width/2)
    center_y = int(screen_height/2 - window_height/2)
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main() 