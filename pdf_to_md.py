import os
import sys
from PyPDF2 import PdfReader
import re

def clean_text(text):
    """Clean and format the extracted text."""
    # Remove multiple newlines
    text = re.sub(r'\n\s*\n', '\n\n', text)
    # Remove extra spaces
    text = re.sub(r' +', ' ', text)
    # Convert to markdown-style headers
    text = re.sub(r'^([A-Z][A-Z\s]+)$', r'## \1', text, flags=re.MULTILINE)
    return text.strip()

def get_default_output_dir():
    """Get the default output directory in the current working directory."""
    default_dir = os.path.join(os.getcwd(), 'converted')
    try:
        os.makedirs(default_dir, exist_ok=True)
        return default_dir
    except PermissionError:
        return os.getcwd()

def ensure_writable_directory(directory):
    """
    Check if directory is writable, if not, try to use default directory.
    
    Args:
        directory (str): Directory path to check
        
    Returns:
        str: Writable directory path
    """
    if directory is None:
        return get_default_output_dir()
        
    try:
        # Test if directory is writable
        test_file = os.path.join(directory, '.write_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        return directory
    except (PermissionError, OSError):
        print(f"Warning: No write permission for directory '{directory}'")
        default_dir = get_default_output_dir()
        print(f"Using directory '{default_dir}' instead")
        return default_dir

def convert_pdf_to_md(pdf_path, output_dir=None):
    """
    Convert a PDF file to Markdown format.
    
    Args:
        pdf_path (str): Path to the PDF file
        output_dir (str, optional): Directory to save the markdown file. If None, saves in the 'converted' subdirectory.
    
    Returns:
        str: Path to the generated markdown file
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Get the base filename without extension
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    # Ensure we have a writable directory
    output_dir = ensure_writable_directory(output_dir)
    
    # Generate output path
    output_path = os.path.join(output_dir, f"{base_name}.md")
    
    try:
        # Read PDF file
        reader = PdfReader(pdf_path)
        
        # Extract text from all pages
        markdown_content = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                markdown_content.append(clean_text(text))
        
        # Join all pages with double newlines
        markdown_content = '\n\n'.join(markdown_content)
        
        # Write the markdown content to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Successfully converted {pdf_path} to {output_path}")
        return output_path
    
    except PermissionError as e:
        print(f"Error: Permission denied when writing to {output_path}")
        print("Please check if you have write permissions for the output directory")
        raise
    except Exception as e:
        print(f"Error converting PDF to Markdown: {str(e)}")
        raise

def main():
    if len(sys.argv) < 2:
        print("Usage: python pdf_to_md.py <pdf_file_path> [output_directory]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        convert_pdf_to_md(pdf_path, output_dir)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 