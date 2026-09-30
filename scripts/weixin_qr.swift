import Foundation
import CoreImage
import AppKit

let input = URL(fileURLWithPath: CommandLine.arguments[1])
let object = try JSONSerialization.jsonObject(with: Data(contentsOf: input)) as! [String: Any]
let content = object["qrcode_img_content"] as! String
let filter = CIFilter(name: "CIQRCodeGenerator")!
filter.setValue(content.data(using: .utf8), forKey: "inputMessage")
filter.setValue("M", forKey: "inputCorrectionLevel")
let code = filter.outputImage!.transformed(by: CGAffineTransform(scaleX: 8, y: 8))
let image = CIContext().createCGImage(code, from: code.extent)!
let bitmap = NSBitmapImageRep(cgImage: image)
try bitmap.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: CommandLine.arguments[2]))
