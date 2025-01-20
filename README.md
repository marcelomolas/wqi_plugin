# WQIPlugin

WQIPlugin is a **QGIS** plugin that allows automatic calculation of the **Water Quality Index (WQI)** using raster data of various physicochemical parameters as input.

## Requirements

- **QGIS**: Version 3.38.2 or higher
- **Dependencies**:
  - `QgsRasterCalculator`
  - Algorithm `gdal:gridinversedistance`

## Installation

### Manual Installation

1. Download the source code from the official repository.
2. Copy the plugin folder to:
   - On Windows: `C:\Users\<user>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins`  
   - On Linux/Mac: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins`
3. Restart QGIS and enable the plugin from the plugin manager.

## Usage

1. Create a QGIS Project
2. Load the project with the raster layers of the physicochemical parameters to be used.
3. If you do not have raster layers but only vector layers, you can use the "Interpolate with IDW ()" to quickly generate raster layers.
4. Access the plugin from the toolbar or `Plugins > WQIPlugin`.
5. Select the input layers and adjust the parameters as needed.
6. Click "Generate WQI" to generate the water quality index raster layer.

## Example of Use

(Add screenshots or step-by-step workflow)

## License

This plugin is distributed under the **GNU General Public License v3.0**.

## Credits

Developed by: **Marcelo Molas and Carin Martínez**

## Contact

To report bugs or suggestions, you can contact us at: **marcemolas@gmail.com or carinme97@gmail.com**

Issue tracker: [GitHub Issues](https://github.com/marcelomolas/wqi_plugin/issues)
