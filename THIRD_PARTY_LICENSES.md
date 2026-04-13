# Third-Party Licenses

Diagram Editor uses the following open-source libraries. Their use does not
affect the proprietary license of Diagram Editor itself.

---

## PySide6

- **Project:** https://doc.qt.io/qtforpython-6/
- **License:** GNU Lesser General Public License v3.0 (LGPL-3.0)
- **Usage:** Qt bindings for the application UI, rendering, and graphics scene

PySide6 is dynamically linked (imported at runtime via Python). Users may
replace it with any compatible version. The LGPL license text is available at:
https://www.gnu.org/licenses/lgpl-3.0.html

---

## fpdf2

- **Project:** https://py-pdf.github.io/fpdf2/
- **License:** GNU Lesser General Public License v3.0 (LGPL-3.0)
- **Usage:** PDF export functionality

fpdf2 is dynamically linked (imported at runtime via Python). Users may
replace it with any compatible version. The LGPL license text is available at:
https://www.gnu.org/licenses/lgpl-3.0.html

---

## PyInstaller (build-time only)

- **Project:** https://pyinstaller.org/
- **License:** GPL v2.0 with special exception for proprietary applications
- **Usage:** Optional build tool for creating standalone executables (not bundled at runtime)

PyInstaller's license includes a special exception that permits building and
distributing non-free (including commercial) applications. See:
https://pyinstaller.org/en/stable/license.html

---

### LGPL-3.0 Compliance Note

This application dynamically links to LGPL-licensed libraries via standard
Python imports. Users may substitute these libraries with modified versions
using pip. No modifications have been made to the source code of any
LGPL-licensed dependency.

The full text of the GNU Lesser General Public License v3.0 is available at:
https://www.gnu.org/licenses/lgpl-3.0.html
