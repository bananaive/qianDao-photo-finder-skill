#!/usr/bin/env swift
import Foundation
import Vision

func emit(_ row: [String: Any]) throws {
    let data = try JSONSerialization.data(withJSONObject: row, options: [.sortedKeys])
    FileHandle.standardOutput.write(data)
    FileHandle.standardOutput.write(Data([10]))
}

let args = CommandLine.arguments
guard args.count == 3 || args.count == 4,
      args[1].range(of: "^[0-9]{3,12}$", options: .regularExpression) != nil,
      args.count == 3 || ["fast", "accurate"].contains(args[3]) else {
    fputs("Usage: swift scan-bibs.swift BIB IMAGE_PATHS.txt [fast|accurate]\n", stderr)
    exit(2)
}

do {
    let bib = args[1]
    let paths = try String(contentsOfFile: args[2], encoding: .utf8)
        .split(whereSeparator: \.isNewline).map(String.init)
    let tokens = try NSRegularExpression(pattern: "(?<![A-Za-z0-9])[0-9]{3,12}(?![A-Za-z0-9])")
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = args.count == 4 && args[3] == "accurate" ? .accurate : .fast
    request.usesLanguageCorrection = false
    var scanned = 0, failed = 0, matches = 0
    for path in paths {
        do {
            try VNImageRequestHandler(url: URL(fileURLWithPath: path)).perform([request])
        } catch {
            failed += 1
            try emit(["type": "error", "image": path])
            continue
        }
        scanned += 1
        let matched = (request.results ?? []).contains { observation in
            observation.topCandidates(3).contains { candidate in
                let text = candidate.string as NSString
                return tokens.matches(in: candidate.string, range: NSRange(location: 0, length: text.length))
                    .contains { text.substring(with: $0.range) == bib }
            }
        }
        if matched {
            matches += 1
            try emit(["type": "match", "image": path, "bib": bib])
        }
    }
    try emit(["type": "summary", "requested": paths.count, "scanned": scanned,
              "failed": failed, "matches": matches])
    if failed > 0 { exit(1) }
} catch {
    fputs("Unable to read the image list or write results.\n", stderr)
    exit(1)
}
