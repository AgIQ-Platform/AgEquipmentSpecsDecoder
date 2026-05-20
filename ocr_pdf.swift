import Foundation
import PDFKit
import Vision
import CoreGraphics

func performOCR(onPdfPath pdfPath: String, maxPages: Int = 5) {
    let url = URL(fileURLWithPath: pdfPath)
    guard let document = PDFDocument(url: url) else {
        print("Failed to open PDF document at \(pdfPath)")
        return
    }
    
    let pageCount = document.pageCount
    print("PDF \(pdfPath) has \(pageCount) pages. OCR-ing first \(min(maxPages, pageCount)) pages...")
    
    for pageIndex in 0..<min(maxPages, pageCount) {
        guard let page = document.page(at: pageIndex) else { continue }
        
        // Render PDF page to CGImage
        let bounds = page.bounds(for: .mediaBox)
        let width = Int(bounds.width * 2.0) // Render at 2x scale for better OCR accuracy
        let height = Int(bounds.height * 2.0)
        
        let colorSpace = CGColorSpaceCreateDeviceRGB()
        guard let context = CGContext(
            data: nil,
            width: width,
            height: height,
            bitsPerComponent: 8,
            bytesPerRow: 0,
            space: colorSpace,
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else {
            print("Failed to create graphics context for page \(pageIndex + 1)")
            continue
        }
        
        // Clear background
        context.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
        context.fill(CGRect(x: 0, y: 0, width: width, height: height))
        
        // Scale and draw PDF page
        context.scaleBy(x: 2.0, y: 2.0)
        page.draw(with: .mediaBox, to: context)
        
        guard let cgImage = context.makeImage() else {
            print("Failed to render page \(pageIndex + 1) to CGImage")
            continue
        }
        
        // Perform OCR using Vision framework
        let requestHandler = VNImageRequestHandler(cgImage: cgImage, options: [:])
        let request = VNRecognizeTextRequest { request, error in
            if let error = error {
                print("OCR Error on page \(pageIndex + 1): \(error)")
                return
            }
            
            guard let observations = request.results as? [VNRecognizedTextObservation] else { return }
            
            print("\n--- PAGE \(pageIndex + 1) OCR ---")
            var pageText = ""
            for observation in observations {
                guard let topCandidate = observation.topCandidates(1).first else { continue }
                pageText += topCandidate.string + "\n"
            }
            print(pageText.trimmingCharacters(in: .whitespacesAndNewlines))
        }
        
        request.recognitionLevel = .accurate
        request.usesLanguageCorrection = true
        
        do {
            try requestHandler.perform([request])
        } catch {
            print("Failed to perform OCR request: \(error)")
        }
    }
}

let arguments = CommandLine.arguments
if arguments.count < 2 {
    print("Usage: swift ocr_pdf.swift <path_to_pdf> [max_pages]")
    exit(1)
}

let pdfPath = arguments[1]
var maxPages = 5
if arguments.count >= 3, let parsed = Int(arguments[2]) {
    maxPages = parsed
}

performOCR(onPdfPath: pdfPath, maxPages: maxPages)
