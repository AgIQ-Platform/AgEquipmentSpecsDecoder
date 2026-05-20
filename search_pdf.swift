import Foundation
import PDFKit
import Vision
import CoreGraphics

func searchPDF(path: String, keywords: [String]) {
    let url = URL(fileURLWithPath: path)
    guard let document = PDFDocument(url: url) else {
        print("Failed to open PDF document at \(path)")
        return
    }
    
    let pageCount = document.pageCount
    print("Searching \(path) (\(pageCount) pages) for keywords: \(keywords)...")
    
    for pageIndex in 0..<pageCount {
        guard let page = document.page(at: pageIndex) else { continue }
        
        let bounds = page.bounds(for: .mediaBox)
        let width = Int(bounds.width * 1.5)
        let height = Int(bounds.height * 1.5)
        
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
            continue
        }
        
        context.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
        context.fill(CGRect(x: 0, y: 0, width: width, height: height))
        
        context.scaleBy(x: 1.5, y: 1.5)
        page.draw(with: .mediaBox, to: context)
        
        guard let cgImage = context.makeImage() else { continue }
        
        let requestHandler = VNImageRequestHandler(cgImage: cgImage, options: [:])
        let request = VNRecognizeTextRequest { request, error in
            if let error = error {
                return
            }
            
            guard let observations = request.results as? [VNRecognizedTextObservation] else { return }
            
            var pageText = ""
            for observation in observations {
                guard let topCandidate = observation.topCandidates(1).first else { continue }
                pageText += topCandidate.string + "\n"
            }
            
            for keyword in keywords {
                if pageText.range(of: keyword, options: .caseInsensitive) != nil {
                    print("\n[MATCH] Found '\(keyword)' on Page \(pageIndex + 1):")
                    // Print lines containing matching text
                    let lines = pageText.components(separatedBy: .newlines)
                    for line in lines {
                        if line.range(of: keyword, options: .caseInsensitive) != nil {
                            print("  > \(line)")
                        }
                    }
                }
            }
        }
        
        request.recognitionLevel = .fast // Fast is fine for searching keyword
        
        do {
            try requestHandler.perform([request])
        } catch {
            print("Failed to perform OCR on page \(pageIndex + 1): \(error)")
        }
    }
}

let args = CommandLine.arguments
if args.count < 3 {
    print("Usage: swift search_pdf.swift <path_to_pdf> <keyword1> [keyword2] ...")
    exit(1)
}

let path = args[1]
let keywords = Array(args[2...])
searchPDF(path: path, keywords: keywords)
