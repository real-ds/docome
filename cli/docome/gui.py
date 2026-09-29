import customtkinter as ctk
import threading
import os
import sys
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog
import io

sys.path.insert(0, str(Path(__file__).parent))

from packages.pdf_engine import PdfEngine, CompressLevel, Rotation
from packages.conversion_engine import ConversionEngine
from packages.signature_engine import SignatureEngine

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class DocomeApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Docome - Document Processor")
        self.geometry("900x700")

        self.pdf_engine = PdfEngine()
        self.conversion_engine = ConversionEngine()
        self.signature_engine = SignatureEngine()

        self.setup_ui()

    def setup_ui(self):
        self.tabview = ctk.CTkTabview(self, fg_color="transparent")
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_pdf = self.tabview.add("PDF Operations")
        self.tab_convert = self.tabview.add("Conversion")
        self.tab_sign = self.tabview.add("E-Signature")

        self.setup_pdf_tab()
        self.setup_convert_tab()
        self.setup_sign_tab()

    def setup_pdf_tab(self):
        frame = ctk.CTkFrame(self.tab_pdf)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="PDF Operations", font=("Arial", 20, "bold")).pack(pady=10)

        self.pdf_file_label = ctk.CTkLabel(frame, text="No file selected")
        self.pdf_file_label.pack(pady=5)

        ctk.CTkButton(frame, text="Select PDF File", command=self.select_pdf_file).pack(pady=5)

        ctk.CTkLabel(frame, text="Operation:").pack(pady=5)
        self.pdf_operation = ctk.CTkComboBox(frame, values=[
            "Merge PDFs", "Split PDF", "Extract Pages", "Remove Pages",
            "Rotate Pages", "Compress", "Get Metadata", "Password Protect"
        ])
        self.pdf_operation.pack(pady=5)
        self.pdf_operation.set("Merge PDFs")

        self.pdf_output_label = ctk.CTkLabel(frame, text="Output file/directory")
        self.pdf_output_label.pack(pady=5)

        ctk.CTkButton(frame, text="Select Output", command=self.select_pdf_output).pack(pady=5)

        ctk.CTkButton(frame, text="Execute", command=self.run_pdf_operation, fg_color="green").pack(pady=10)

        self.pdf_status = ctk.CTkLabel(frame, text="")
        self.pdf_status.pack(pady=5)

    def setup_convert_tab(self):
        frame = ctk.CTkFrame(self.tab_convert)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="Document Conversion", font=("Arial", 20, "bold")).pack(pady=10)

        self.convert_file_label = ctk.CTkLabel(frame, text="No file selected")
        self.convert_file_label.pack(pady=5)

        ctk.CTkButton(frame, text="Select File", command=self.select_convert_file).pack(pady=5)

        ctk.CTkLabel(frame, text="Conversion:").pack(pady=5)
        self.convert_type = ctk.CTkComboBox(frame, values=[
            "PDF -> DOCX", "DOCX -> PDF", "PDF -> TXT", "PDF -> Markdown",
            "PDF -> XLSX", "XLSX -> PDF", "PDF -> PNG"
        ])
        self.convert_type.pack(pady=5)
        self.convert_type.set("PDF -> DOCX")

        ctk.CTkButton(frame, text="Convert", command=self.run_convert_operation, fg_color="green").pack(pady=10)

        self.convert_status = ctk.CTkLabel(frame, text="")
        self.convert_status.pack(pady=5)

    def setup_sign_tab(self):
        frame = ctk.CTkFrame(self.tab_sign)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="E-Signature", font=("Arial", 20, "bold")).pack(pady=10)

        self.sign_file_label = ctk.CTkLabel(frame, text="No PDF selected")
        self.sign_file_label.pack(pady=5)

        ctk.CTkButton(frame, text="Select PDF", command=self.select_sign_file).pack(pady=5)

        ctk.CTkLabel(frame, text="Signature Type:").pack(pady=5)
        self.sign_type = ctk.CTkComboBox(frame, values=[
            "Create Typed Signature", "Add Signature to PDF"
        ])
        self.sign_type.pack(pady=5)
        self.sign_type.set("Create Typed Signature")

        ctk.CTkLabel(frame, text="Name for signature:").pack(pady=5)
        self.sign_name = ctk.CTkEntry(frame, placeholder_text="Enter name")
        self.sign_name.pack(pady=5)

        ctk.CTkButton(frame, text="Create/Add Signature", command=self.run_sign_operation, fg_color="green").pack(pady=10)

        self.sign_status = ctk.CTkLabel(frame, text="")
        self.sign_status.pack(pady=5)

    def select_pdf_file(self):
        file = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file:
            self.pdf_file = file
            self.pdf_file_label.configure(text=Path(file).name)

    def select_pdf_output(self):
        operation = self.pdf_operation.get()
        if operation in ["Merge PDFs", "Split PDF"]:
            directory = filedialog.askdirectory()
            if directory:
                self.pdf_output = directory
                self.pdf_output_label.configure(text=directory)
        else:
            file = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
            if file:
                self.pdf_output = file
                self.pdf_output_label.configure(text=Path(file).name)

    def select_convert_file(self):
        file = filedialog.askopenfilename()
        if file:
            self.convert_file = file
            self.convert_file_label.configure(text=Path(file).name)

    def select_sign_file(self):
        file = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file:
            self.sign_file = file
            self.sign_file_label.configure(text=Path(file).name)

    def run_pdf_operation(self):
        def task():
            try:
                operation = self.pdf_operation.get()
                self.pdf_status.configure(text="Processing...")

                if operation == "Merge PDFs":
                    files = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
                    if files:
                        self.pdf_engine.merge(list(files), self.pdf_output)
                        self.pdf_status.configure(text="PDFs merged successfully!")

                elif operation == "Split PDF":
                    self.pdf_engine.split(self.pdf_file, self.pdf_output)
                    self.pdf_status.configure(text=f"Split into files in {self.pdf_output}")

                elif operation == "Extract Pages":
                    pages = simpledialog.askstring("Pages", "Enter pages (e.g., 1-3 or 1,3,5)")
                    if pages:
                        page_list = [int(p.strip()) - 1 for p in pages.split(",")]
                        self.pdf_engine.extract(self.pdf_file, self.pdf_output, pages=page_list)
                        self.pdf_status.configure(text="Pages extracted!")

                elif operation == "Remove Pages":
                    pages = simpledialog.askstring("Pages", "Enter pages to remove (e.g., 1,3,5)")
                    if pages:
                        page_list = [int(p.strip()) - 1 for p in pages.split(",")]
                        self.pdf_engine.remove(self.pdf_file, self.pdf_output, pages=page_list)
                        self.pdf_status.configure(text="Pages removed!")

                elif operation == "Rotate Pages":
                    angle = simpledialog.askinteger("Angle", "Enter angle (90, 180, or 270)")
                    if angle:
                        rotation = Rotation.ROTATE_90 if angle == 90 else (Rotation.ROTATE_180 if angle == 180 else Rotation.ROTATE_270)
                        self.pdf_engine.rotate(self.pdf_file, self.pdf_output, rotation)
                        self.pdf_status.configure(text=f"Rotated {angle} degrees!")

                elif operation == "Compress":
                    self.pdf_engine.compress(self.pdf_file, self.pdf_output, CompressLevel.RECOMMENDED)
                    self.pdf_status.configure(text="PDF compressed!")

                elif operation == "Get Metadata":
                    meta = self.pdf_engine.get_metadata(self.pdf_file)
                    info = f"Title: {meta.title or 'N/A'}\nAuthor: {meta.author or 'N/A'}"
                    messagebox.showinfo("Metadata", info)
                    self.pdf_status.configure(text="Metadata retrieved")

                elif operation == "Password Protect":
                    password = simpledialog.askstring("Password", "Enter password:", show="*")
                    if password:
                        self.pdf_engine.protect(self.pdf_file, self.pdf_output, password)
                        self.pdf_status.configure(text="PDF protected!")

            except Exception as e:
                self.pdf_status.configure(text=f"Error: {str(e)}")

        threading.Thread(target=task).start()

    def run_convert_operation(self):
        def task():
            try:
                conv_type = self.convert_type.get()
                self.convert_status.configure(text="Converting...")

                output = filedialog.asksaveasfilename()
                if not output:
                    return

                if conv_type == "PDF -> DOCX":
                    self.conversion_engine.pdf_to_docx(self.convert_file, output)
                elif conv_type == "DOCX -> PDF":
                    self.conversion_engine.docx_to_pdf(self.convert_file, output)
                elif conv_type == "PDF -> TXT":
                    self.conversion_engine.pdf_to_text(self.convert_file, output)
                elif conv_type == "PDF -> Markdown":
                    self.conversion_engine.pdf_to_markdown(self.convert_file, output)
                elif conv_type == "PDF -> XLSX":
                    self.conversion_engine.pdf_to_xlsx(self.convert_file, output)
                elif conv_type == "XLSX -> PDF":
                    self.conversion_engine.xlsx_to_pdf(self.convert_file, output)
                elif conv_type == "PDF -> PNG":
                    output_dir = filedialog.askdirectory()
                    if output_dir:
                        self.conversion_engine.pdf_to_images(self.convert_file, output_dir)
                        output = output_dir

                self.convert_status.configure(text=f"Converted! Saved to: {output}")

            except Exception as e:
                self.convert_status.configure(text=f"Error: {str(e)}")

        threading.Thread(target=task).start()

    def run_sign_operation(self):
        def task():
            try:
                sign_type = self.sign_type.get()
                self.sign_status.configure(text="Processing...")

                if sign_type == "Create Typed Signature":
                    name = self.sign_name.get()
                    if not name:
                        self.sign_status.configure(text="Please enter a name")
                        return

                    output = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
                    if output:
                        sig_data = self.signature_engine.create_typed_signature(name)
                        Path(output).write_bytes(sig_data)
                        self.sign_status.configure(text=f"Signature saved to: {output}")

                elif sign_type == "Add Signature to PDF":
                    if not hasattr(self, 'sign_file'):
                        self.sign_status.configure(text="Please select a PDF")
                        return

                    sig_file = filedialog.askopenfilename(filetypes=[("PNG", "*.png")])
                    if sig_file:
                        output = filedialog.asksaveasfilename(defaultextension=".pdf")
                        if output:
                            with open(sig_file, "rb") as f:
                                sig_data = f.read()

                            self.signature_engine.add_signature(self.sign_file, output, sig_data, page=1, x=100, y=600)
                            self.sign_status.configure(text=f"Signature added to: {output}")

            except Exception as e:
                self.sign_status.configure(text=f"Error: {str(e)}")

        threading.Thread(target=task).start()


if __name__ == "__main__":
    app = DocomeApp()
    app.mainloop()
