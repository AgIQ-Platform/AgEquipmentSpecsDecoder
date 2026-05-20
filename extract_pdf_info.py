import os
import pypdf

def analyze_pdf(path):
    print(f"\n=========================================")
    print(f"ANALYZING PDF: {os.path.basename(path)}")
    print(f"=========================================")
    
    if not os.path.exists(path):
        print("File does not exist.")
        return
        
    reader = pypdf.PdfReader(path)
    num_pages = len(reader.pages)
    print(f"Total Pages: {num_pages}")
    
    # Extract outline if available
    try:
        outline = reader.outline
        if outline:
            print("\nOutline / Table of Contents (Partial):")
            for item in outline[:10]:
                if isinstance(item, list):
                    print("  [Sub-items exist]")
                else:
                    print(f"  - {item.title}")
        else:
            print("\nNo PDF outline available.")
    except Exception as e:
        print(f"Could not read outline: {e}")
        
    # Extract first 3 pages of text to see what they contain
    print("\n--- FIRST 3 PAGES CONTENT ---")
    for i in range(min(3, num_pages)):
        text = reader.pages[i].extract_text()
        print(f"\n--- Page {i+1} ---")
        lines = text.split('\n')
        for line in lines[:30]:  # Limit lines per page
            print(line)
        if len(lines) > 30:
            print("...")

if __name__ == "__main__":
    analyze_pdf("Book1.pdf")
    analyze_pdf("Book2.pdf")
