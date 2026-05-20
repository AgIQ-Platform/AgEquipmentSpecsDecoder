import pypdf

def check_pdf(path):
    print(f"\nChecking elements in {path}:")
    reader = pypdf.PdfReader(path)
    page = reader.pages[0]
    
    # Check if there are any images in the resources
    if "/XObject" in page.resources:
        xobjects = page.resources["/XObject"]
        for obj in xobjects:
            if xobjects[obj]["/Subtype"] == "/Image":
                print(f"  - Found image object: {obj}")
                
    # Print the raw text of the first page to see if there are any characters
    text = page.extract_text()
    print(f"  - Extracted text length: {len(text.strip())}")

if __name__ == "__main__":
    check_pdf("Book1.pdf")
    check_pdf("Book2.pdf")
