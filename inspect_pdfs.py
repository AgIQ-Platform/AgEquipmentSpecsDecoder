import os

def test_imports():
    libs = ['pypdf', 'pdfplumber', 'fitz', 'PyPDF2']
    print("Checking PDF libraries:")
    for lib in libs:
        try:
            __import__(lib)
            print(f"  - {lib}: AVAILABLE")
        except ImportError:
            print(f"  - {lib}: NOT AVAILABLE")

if __name__ == "__main__":
    test_imports()
