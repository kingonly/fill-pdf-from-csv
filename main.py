import tkinter as tk
from tkinter import ttk, filedialog
from pdf_viewer import PDFViewer

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Form Editor")
        
        # Create main toolbar frame
        self.toolbar = ttk.Frame(root)
        self.toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Create Open PDF button
        self.open_btn = ttk.Button(self.toolbar, text="Open PDF", 
                                  command=self.open_pdf)
        self.open_btn.pack(side=tk.LEFT, padx=5)
    
    def open_pdf(self):
        pdf_path = filedialog.askopenfilename(
            title="Select PDF",
            filetypes=[("PDF files", "*.pdf")]
        )
        
        if pdf_path:
            # Hide the Open PDF button
            self.open_btn.pack_forget()
            
            # Create the PDF viewer
            self.viewer = PDFViewer(self.root, pdf_path)

def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main() 