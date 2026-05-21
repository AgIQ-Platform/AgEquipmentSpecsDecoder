import os

def merge():
    print("=== Inlining CSS and JS into index.html ===")
    
    html_path = "static/index.html"
    css_path = "static/index.css"
    js_path = "static/app.js"
    
    # Read files
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
        
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()
        
    with open(js_path, "r", encoding="utf-8") as f:
        js = f.read()
        
    # Replace CSS link with inline style tag
    css_target = '<link rel="stylesheet" href="/static/index.css">'
    css_replacement = f"<style>\n{css}\n</style>"
    if css_target in html:
        html = html.replace(css_target, css_replacement)
        print("Successfully inlined CSS stylesheet.")
    else:
        print("Warning: CSS stylesheet target tag not found in HTML!")
        
    # Replace JS script tag with inline script tag
    js_target = '<script src="/static/app.js"></script>'
    js_replacement = f"<script>\n{js}\n</script>"
    if js_target in html:
        html = html.replace(js_target, js_replacement)
        print("Successfully inlined JavaScript bundle.")
    else:
        print("Warning: JS script tag target not found in HTML!")
        
    # Write back to index.html
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print("Merge complete! static/index.html is now 100% self-contained.")

if __name__ == "__main__":
    merge()
