# Windows 7 Compatibility

## Feature Integrity

Due to system limitations on Windows 7, some features cannot be fully enabled on this platform.  
The following list summarizes the confirmed missing or limited functionalities:

### Theme-Related

-   System theme synchronization is **not supported**; only manual switching between light and dark themes is available.
    
-   **HiDPI** (High DPI) display support is unavailable.
    

### Internationalization (I18N) String Collection

-   Some older versions of **PySide6** do **not include** the `lupdate` executable, which prevents automatic collection of translation strings (generation of `.ts` files).
    
-   **Workaround:**  
    Add the directory containing your custom `lupdate` executable to the system `PATH` environment variable, so that `pyside-cli` can detect it properly.
    

### Nuitka Build Backend

-   Compilation and packaging with Nuitka are theoretically possible, but the generated applications **may fail to run properly** on Windows 7.
    

---

## Usage Notes

This project provides **PyInstaller** as a compatibility build backend for Windows 7.  
You can enable this mode by adding the `--backend pyinstaller` flag when running commands:

```bash
uv run pyside-cli --all --onefile --backend pyinstaller --low-perf
```

### Build Recommendations

Packaging on Windows 7 may encounter toolchain incompatibility issues.  
It is recommended to follow one of the approaches below:

1.  **Preferred approach:**  
    Perform development and builds on a newer Windows platform, then test on the target Windows 7 system.
    
2.  **Alternative approaches:**
    
    -   Downgrade specific toolchain versions to regain compatibility.
        
    -   Use compatibility layers such as [VxKex](https://github.com/i486/VxKex) to run build tools.
        

Additionally, since Windows 7 often runs on older hardware,  
it’s recommended to include the `--low-perf` flag in your build command to disable certain high-performance features,  
improving overall stability and compatibility.
