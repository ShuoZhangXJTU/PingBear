// 本地 OCR：把论文截图里的文字取出来（macOS Vision，无需联网、不调云服务）。
// 用法: swift ocr.swift <图片> [语言,用逗号分隔]
import Foundation
import Vision
import AppKit

let args = CommandLine.arguments
guard args.count > 1 else {
    FileHandle.standardError.write("usage: swift ocr.swift <image> [languages]\n".data(using: .utf8)!)
    exit(2)
}
guard let image = NSImage(contentsOfFile: args[1]),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    FileHandle.standardError.write("cannot read image: \(args[1])\n".data(using: .utf8)!)
    exit(3)
}
let languages = args.count > 2 ? args[2].split(separator: ",").map(String.init) : ["en-US", "zh-Hans"]
// Vision rejects some source formats (e.g. 420f JPEG); normalise to RGBA first.
let width = cgImage.width, height = cgImage.height
guard let context = CGContext(data: nil, width: width, height: height, bitsPerComponent: 8,
    bytesPerRow: 0, space: CGColorSpaceCreateDeviceRGB(),
    bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else {
    FileHandle.standardError.write("cannot create bitmap context\n".data(using: .utf8)!)
    exit(5)
}
context.draw(cgImage, in: CGRect(x: 0, y: 0, width: width, height: height))
guard let normalised = context.makeImage() else {
    FileHandle.standardError.write("cannot normalise image\n".data(using: .utf8)!)
    exit(6)
}
let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = languages
request.usesLanguageCorrection = true
do {
    try VNImageRequestHandler(cgImage: normalised, options: [:]).perform([request])
} catch {
    FileHandle.standardError.write("ocr failed: \(error)\n".data(using: .utf8)!)
    exit(4)
}
let lines = (request.results ?? []).compactMap { $0.topCandidates(1).first?.string }
print(lines.joined(separator: "\n"))
