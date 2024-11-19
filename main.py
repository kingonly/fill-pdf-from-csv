import tkinter as tk
from tkinter import filedialog
from pdf_viewer import PDFViewer

def main():
    # Create the main window
    root = tk.Tk()
    root.title("PDF Viewer")
    
    # Create a function to handle file selection
    def select_pdf():
        file_path = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if file_path:  # Only create viewer if a file was selected
            viewer = PDFViewer(root, file_path)
    
    # Create a button to open file dialog
    select_button = tk.Button(root, text="Open PDF", command=select_pdf)
    select_button.pack(pady=20)
    
    # Start the application
    root.mainloop()

if __name__ == "__main__":
    main() 