# ComfyUI PNG to JPG Converter

Transform your ComfyUI workflow collection from storage-hungry PNGs to efficient JPGs while preserving all your precious workflow metadata.

## 🚀 Why You Need This

If you're a ComfyUI user, you know the pain:
- **Massive PNG files** eating up your storage (often 10-50MB+ each)
- **Hundreds of nearly-identical workflow JSONs** cluttering your folders
- **Can't share images** on social media without losing embedded workflows
- **Storage costs** mounting up as your collection grows

This tool solves all of these problems in one intelligent batch operation.

## ✨ What It Does

- **Converts PNG → JPG** with customizable quality settings
- **Extracts ComfyUI workflows** to separate JSON files
- **Smart deduplication** - only saves unique workflows (ignores seed changes)
- **Preserves workflow functionality** - drag & drop JSON files back into ComfyUI
- **Batch processes** entire directory trees recursively
- **Reports space savings** so you can see the impact
- **Cleans up macOS junk files** (optional)

## 📊 Real Results

Typical space savings:
- **PNG with workflow**: 25-50MB per image
- **JPG + JSON**: 2-5MB per image  
- **Space reduction**: 80-90% smaller files
- **1000 images**: Save 20-45GB of storage

## 🔧 Installation

### Prerequisites
- Python 3.6+
- ImageMagick (for JPG conversion)

### Install ImageMagick

**macOS (Homebrew):**
```bash
brew install imagemagick
```

**Ubuntu/Debian:**
```bash
sudo apt-get install imagemagick
```

**Windows:**
Download from [ImageMagick.org](https://imagemagick.org/script/download.php#windows)

### Install Python Dependencies
```bash
pip install -r requirements.txt
```

## 🏃 Quick Start

Convert all PNGs in a directory:
```bash
python convert_png_jpg_json.py /path/to/your/comfyui/outputs
```

Convert with custom quality and delete originals:
```bash
python convert_png_jpg_json.py /path/to/outputs -q 95 -d
```

## 📖 Usage

### Basic Usage
```bash
python convert_png_jpg_json.py <source_directory> [options]
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `-q, --quality` | JPEG quality (0-100) | 85 |
| `-d, --delete-original` | Delete original PNG files | False |
| `-m, --clean-mac-files` | Remove macOS `._` junk files | False |
| `-v, --verbose` | Detailed output for each file | False |
| `-s, --silent` | Suppress progress output | False |
| `--inspect <file>` | Debug PNG metadata structure | - |

### Examples

**High quality conversion:**
```bash
python convert_png_jpg_json.py ./outputs -q 95
```

**Space-saving mode (delete originals):**
```bash
python convert_png_jpg_json.py ./outputs -d
```

**Clean up everything:**
```bash
python convert_png_jpg_json.py ./outputs -d -m -q 90
```

**Verbose debugging:**
```bash
python convert_png_jpg_json.py ./outputs -v
```

**Inspect a specific file:**
```bash
python convert_png_jpg_json.py --inspect ./outputs/ComfyUI_12345_.png
```

## 🧠 Smart Workflow Detection

The tool intelligently compares workflows and only creates JSON files when there are meaningful changes:

✅ **Creates JSON for:**
- New node configurations
- Different parameters
- Changed connections
- Modified prompts

❌ **Skips JSON for:**
- Only seed value changes
- Identical workflows with different random seeds
- Control setting changes (randomize/fixed)

## 📁 Output Structure

**Before:**
```
outputs/
├── ComfyUI_12345_.png (45MB, workflow embedded)
├── ComfyUI_12346_.png (44MB, same workflow, different seed)
└── ComfyUI_12347_.png (46MB, new workflow)
```

**After:**
```
outputs/
├── ComfyUI_12345_.jpg (3MB)
├── ComfyUI_12345_.json (workflow data)
├── ComfyUI_12346_.jpg (3MB)
└── ComfyUI_12347_.jpg (3MB)
└── ComfyUI_12347_.json (new workflow data)
```

## 🔄 Workflow Preservation

Your workflows remain fully functional:
1. **Drag & drop** JSON files into ComfyUI to load workflows
2. **All node connections** and parameters preserved
3. **Compatible** with ComfyUI's native format
4. **No data loss** - everything is preserved

## 📈 Sample Output

```
Starting conversion in 'outputs' (Quality: 85%, Delete Original: False, Clean Mac Files: False)...
--------------------------------------------------
  ComfyUI_12485_.png: JPG created, JSON created
  ComfyUI_12486_.png: JPG created
  ComfyUI_12487_.png: JPG created
  ComfyUI_12488_.png: JPG created
    ...
  ComfyUI_12491_.png: JPG created, JSON created
  ComfyUI_12492_.png: JPG created
--------------------------------------------------
Conversion Summary:
  Converted: 28 files
  JSON files created: 4 files
  Skipped:   0 files (JPG already existed)
  Errors:    0 files
  Total Space Saved: 1.2 GB
Conversion complete.
```

## 🛠️ Troubleshooting

### Common Issues

**"convert command not found"**
- Install ImageMagick (see installation section)
- Make sure it's in your PATH

**"Could not identify image format"**
- File may be corrupted or not a valid PNG
- Use `--inspect` to debug the file

**"No workflow metadata found"**
- PNG wasn't generated by ComfyUI
- Or workflow embedding was disabled in ComfyUI

**Permission errors**
- Check file/directory permissions
- Run with appropriate user privileges

## 🎯 Perfect For

- **ComfyUI power users** with large image collections
- **AI artists** sharing work on social media
- **Workflow collectors** organizing and archiving
- **Storage-conscious users** managing disk space
- **Teams** sharing workflows without massive files

## 🤝 Contributing

Found a bug? Have a feature request? Contributions welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - feel free to use and modify as needed.

## 🌟 Support

If this tool saved you storage space and headaches, consider:
- ⭐ Starring the repository
- 🐛 Reporting issues
- 💡 Suggesting improvements
- 📢 Sharing with the ComfyUI community

---

**Transform your ComfyUI workflow collection today - your storage drive will thank you!**
