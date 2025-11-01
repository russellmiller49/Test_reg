# iOS App (Preserved for Future Development)

This directory contains the iOS/Swift portion of the bronchoscopy registry project, preserved for potential future development.

## 📱 Contents

- `Bronch_registryApp.swift` - iOS app entry point (SwiftUI)
- `ContentView.swift` - Main SwiftUI view
- `Assets.xcassets/` - iOS asset catalog (app icons, colors)

## 🎯 Purpose

The iOS app was originally designed to:
- Capture clinical notes via iOS camera
- Perform on-device OCR using VisionKit
- Detect and redact PHI on-device
- Extract structured data using Apple's Foundation Models (iOS 26+)
- Submit de-identified data to the registry gateway

## 📋 Status

**Current Status:** Basic SwiftUI structure (minimal implementation)

The iOS app was planned but development has been paused in favor of the web-based version. The files are preserved here for:
1. Future iOS development if desired
2. Reference for understanding the original architecture
3. Potential extraction of extraction logic/prompts

## 🔄 Integration with Main Project

The iOS app would use:
- **Schema:** `../schemas/bronchoscopy_procedure.schema.json` (shared)
- **Backend API:** `../api/` (shared FastAPI backend)
- **Data Models:** Would need Swift equivalents of `../bronch_schema/models.py`

## 📚 Related Documentation

See the main project README and `REGISTRY_MASTER_PLAN.md` for:
- Complete implementation specifications
- Extraction prompts and logic
- Architecture details
- Schema definitions

## 🛠️ Future Development

If resuming iOS development:

1. **Create Xcode Project**
   ```bash
   # In this directory
   # Create new Xcode project targeting iOS 26+
   # Add these Swift files to the project
   ```

2. **Implement Extraction Service**
   - Port extraction logic from `REGISTRY_MASTER_PLAN.md`
   - Use Apple Foundation Models framework
   - Implement `ExtractionService` class (see master plan)

3. **Add OCR & PHI Detection**
   - VisionKit for OCR
   - Regex-based PHI detection (see `config/phi_rules.json` in master plan)
   - Pixel-level redaction

4. **Integrate with Backend**
   - Connect to `../api/` FastAPI backend
   - Submit structured data matching the schema

## 📝 Notes

- Requires iOS 26+ (for Foundation Models)
- Requires Xcode 16+ (for Swift 6 and Foundation Models)
- On-device processing ensures privacy (no PHI sent to servers)

---

**Last Updated:** Preserved during transition to web-focused development

