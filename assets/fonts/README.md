# Bundled open fonts

These fonts may be redistributed with this project and embedded in PDFs under the SIL Open Font License 1.1. Keep the accompanying license files with copies of the font software.

- **Source Serif 4**: Adobe; the regular and semibold TTF files are unmodified official release files. See `OFL-SourceSerif4.md`.
- **Source Sans 3**: Adobe; the regular and semibold TTF files are unmodified official release files. See `OFL-SourceSans3.md`.
- **Noto Sans SC**: Google / Adobe; full Simplified Chinese coverage, also containing many traditional characters. See `OFL-NotoSansSC.txt`.

Noto Sans SC was instantiated from the official variable TTF at `wght=400` using fontTools 4.61.1 (`instantiateVariableFont`), then its style/name entries were set to Regular. Copyright and license metadata are preserved. It is a static TrueType font suitable for ReportLab embedding; no system font or network access is needed during builds. No character subset was applied. A missing character fails the PDF build explicitly rather than emitting a blank glyph.

Fonts were retrieved on 2026-09-10. Source URLs and checksums of the bundled files:

- [SourceSerif4-Regular.ttf](https://raw.githubusercontent.com/adobe-fonts/source-serif/release/TTF/SourceSerif4-Regular.ttf)
  - SHA-256: `e5a4ee6a3d87bb9024796be390c6771e2a0eb1883dae25effaf57ca01668e24b`
- [SourceSerif4-Semibold.ttf](https://raw.githubusercontent.com/adobe-fonts/source-serif/release/TTF/SourceSerif4-Semibold.ttf)
  - SHA-256: `36db62940cb5728b12b1802476dc7fcf4c6c519a7bdd476ba23a4e555fc4655f`
- [SourceSans3-Regular.ttf](https://raw.githubusercontent.com/adobe-fonts/source-sans/release/TTF/SourceSans3-Regular.ttf)
  - SHA-256: `4644c81b86ec9caaa76b634889968ed3c4f4f52f054855933acc7c2b21e53b0f`
- [SourceSans3-Semibold.ttf](https://raw.githubusercontent.com/adobe-fonts/source-sans/release/TTF/SourceSans3-Semibold.ttf)
  - SHA-256: `a3f4f8dcf343a8f24dc61951de93f3ba1558b15cd250ba24af8a40e957081b7d`
- [NotoSansSC-Regular.ttf](https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/Variable/TTF/Subset/NotoSansSC-VF.ttf)
  - SHA-256: `21add0648574b774a301b0d081dffc0e0c24022d71ed0fcc90921bfe286d0d97`

License sources:

- https://raw.githubusercontent.com/adobe-fonts/source-serif/release/LICENSE.md
- https://raw.githubusercontent.com/adobe-fonts/source-sans/release/LICENSE.md
- https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/LICENSE

The runtime renderer only needs the bundled static TTFs and ReportLab. fontTools is not a runtime or CI dependency.
