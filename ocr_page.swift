import Foundation
import PDFKit
import Vision
import CoreGraphics

func performOCR(onPdfPath pdfPath: String, pageNum: Int) {
    let url = URL(fileURLWithPath: pdfPath)
    guard let document = PDFDocument(url: url) else {
        print("Failed to open PDF document at \(pdfPath)")
        return
    }
    
    let pageCount = document.pageCount
    guard pageNum >= 1 && pageNum <= pageCount else {
        print("Invalid page number \(pageNum). Document has \(pageCount) pages.")
        return
    }
    
    guard let page = document.page(at: pageNum - 1) else {
        print("Failed to get page \(pageNum)")
        return
    }
    
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
        print("Failed to create graphics context")
        return
    }
    
    // Clear background
    context.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
    context.fill(CGRect(x: 0, y: 0, width: width, height: height))
    
    // Scale and draw PDF page
    context.scaleBy(x: 2.0, y: 2.0)
    page.draw(with: .mediaBox, to: context)
    
    guard let cgImage = context.makeImage() else {
        print("Failed to render page to CGImage")
        return
    }
    
    // Perform OCR using Vision framework
    let requestHandler = VNImageRequestHandler(cgImage: cgImage, options: [:])
    let request = VNRecognizeTextRequest { request, error in
        if let error = error {
            print("OCR Error: \(error)")
            return
        }
        
        guard let observations = request.results as? [VNRecognizedTextObservation] else { return }
        
        print("\n--- PAGE \(pageNum) OCR ---")
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

let arguments = CommandLine.arguments
if arguments.count < 3 {
    print("Usage: swift ocr_page.swift <path_to_pdf> <page_num>")
    exit(1)
}

let pdfPath = arguments[1]
guard let pageNum = Int(arguments[2]) else {
    print("Page number must be an integer")
    exit(1)
}

performOCR(onPdfPath: pdfPath, pageNum: pageNum)
