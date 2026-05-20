import pypdf

def find_first_text_page(path):
    print(f"\nSearching for text in {path}:")
    reader = pypdf.PdfReader(path)
    total_pages = len(reader.pages)
    
    found = False
    for page_num in range(total_pages):
        text = reader.pages[page_num].extract_text()
        if text and len(text.strip()) > 50:
            print(f"  - First page with text is Page {page_num + 1}")
            print(f"  - Text snippet (first 500 chars):")
            print(text.strip()[:800])
            found = True
            break
            
    if not found:
        print("  - No page contains extractable text. The PDF might be scanned/image-only.")

if __name__ == "__main__":
    find_first_text_page("Book1.pdf")
    find_first_text_page("Book2.pdf")
